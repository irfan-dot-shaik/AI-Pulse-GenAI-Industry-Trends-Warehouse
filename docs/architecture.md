# AI Pulse — Architecture Reference (Week 1 + 2)

## System Architecture

```
+----------------------------------------------------------------------+
|                    AI PULSE — WEEK 2 ARCHITECTURE                    |
|      GNews API -> Validate -> Score -> PostgreSQL -> Dashboard       |
+----------------------------------------------------------------------+

  +---------------------+
  |     DATA SOURCE     |
  |                     |
  |   GNews API         |   <- External REST API (HTTP/HTTPS)
  |   gnews.io          |      Returns JSON with AI news articles
  |   Free Tier: 100    |      100 requests/day on free plan
  |   req/day           |
  +----------+----------+
             |
             |  HTTP GET Request
             |  (requests library)
             v
  +---------------------+
  |   INGESTION LAYER   |
  |                     |
  |  ingestion/         |   <- Responsible for fetching data only
  |    gnews_client.py  |      Error handling + retry logic
  |                     |      Returns pd.DataFrame
  +----------+----------+
             |
             |  JSON -> Pandas DataFrame
             v
  +---------------------+
  |   RAW LAYER         |
  |                     |
  |  database/          |   <- Stores data EXACTLY as received
  |    models.py        |      No modifications ever made
  |    warehouse.py     |      Permanent audit trail
  |                     |
  |  raw_ai_news table  |
  +----------+----------+
             |
             |  Read raw DataFrame
             v
  +---------------------+
  |  PROCESSING LAYER   |  <- NEW in Week 2
  |                     |
  |  processing/        |
  |    validator.py     |   -> 5 data quality rules
  |    transformer.py   |   -> Text normalization
  |    scorer.py        |   -> AI Intelligence Score 0-100
  +----------+----------+
             |
             |  Scored, clean DataFrame
             v
  +---------------------+
  |  STAGING LAYER      |  <- NEW in Week 2
  |                     |
  |  stg_ai_news table  |   <- Clean, scored, validated
  |                     |      Re-derivable from raw at any time
  +----------+----------+
             |
             v
  +---------------------+
  |  ANALYTICS LAYER    |  <- NEW in Week 2
  |                     |
  |  analytics/         |
  |    queries.py       |   <- 10 SQL analytics functions
  |                     |
  |  dashboard/         |   <- Streamlit UI
  |    app.py + pages   |
  +---------------------+


  CROSS-CUTTING CONCERNS (Applied Everywhere)
  +--------------------------------------------------------+
  |                                                        |
  |  config/settings.py  <- Single source of config truth |
  |  utils/logger.py     <- Centralized logging           |
  |  tests/              <- Unit tests (no API needed)     |
  |  .env                <- All secrets (never committed)  |
  |                                                        |
  +--------------------------------------------------------+
```

---

## Week 2 — Warehouse Layer Architecture

### Why Two Layers? (Raw + Staging)

A production data warehouse never has just one layer. Here is the reasoning
followed by every serious data engineering team in the world:

```
GNews API
    |
    v
raw_ai_news   <-- NEVER MODIFIED AFTER INSERT (audit trail)
    |
Validation    <-- Remove incomplete records
    |
Transformation <-- Normalize text, fix encoding
    |
AI Intelligence Score <-- Rule-based scoring (0-100)
    |
    v
stg_ai_news   <-- Clean, scored, queryable (derived from raw)
    |
    v
Analytics & Dashboard
```

### The Raw Layer — Why We Never Modify It

**Rule:** Once a record lands in `raw_ai_news`, it is never updated or deleted.

**Reasons:**

1. **Audit Trail**
   Every data decision downstream (cleaning, scoring, filtering) can be
   traced back to the original source record. If an analyst questions a
   score, you can always show them the exact raw data it was derived from.

2. **Debugging**
   If a bug is found in the transformation or scoring logic, you do NOT
   need to call the GNews API again to fix it. You already have the raw
   data. Fix the code, re-run processing from raw. This saves API quota
   and makes the pipeline deterministic.

3. **Regulatory Compliance**
   In real businesses (finance, healthcare, media), regulators often require
   that you keep the original data exactly as received. Modifying raw data
   is considered a compliance violation in many industries.

4. **Multiple Downstream Consumers**
   In Week 3+, other teams might build different staging tables from the
   same raw data — for example, a sentiment analysis staging table and a
   keyword extraction staging table — both derived from the same raw_ai_news.
   If you modified the raw layer, you would break all of them.

### The Staging Layer — Why It Is Re-derived (Not Re-fetched)

**Question:** Why not just call the GNews API again and load fresh data?

**Answer:** The API would return *today's* articles, not the historical ones.

The staging layer is always built *from the raw layer*, not from the API.
This means:

```
Correct flow:
  raw_ai_news -> [process] -> stg_ai_news   (deterministic, reproducible)

Wrong flow:
  GNews API -> [process] -> stg_ai_news     (you lose historical records)
```

**Benefits of re-deriving from raw:**

| Benefit | Explanation |
|---|---|
| **Deterministic** | Same raw data always produces same staging data |
| **API quota safe** | You do not waste API calls on data you already have |
| **Historical coverage** | All past articles get re-scored when you improve the algorithm |
| **Idempotent** | Running the process twice produces the same result |

### Real-World Data Engineering Best Practices Followed

| Practice | How We Apply It |
|---|---|
| **Immutable raw layer** | `raw_ai_news` is insert-only — no UPDATE or DELETE |
| **Layer separation** | `raw_` → `stg_` → analytics (clear naming convention) |
| **Re-derivability** | Staging can always be dropped and rebuilt from raw |
| **Idempotency** | `ON CONFLICT DO NOTHING` on both tables |
| **Fail fast** | Pipeline validates config at startup before touching the DB |
| **Schema as code** | Tables defined in Python (SQLAlchemy) — no manual SQL |
| **Separation of concerns** | Each module does exactly one thing |
| **Single source of truth** | All settings in `config/settings.py` only |

---

## Module Dependency Graph

```
main.py
  |-- config/settings.py          (validate_config)
  |-- ingestion/gnews_client.py   (fetch_ai_news)
  |     |-- config/settings.py
  |     +-- utils/logger.py
  |-- database/warehouse.py       (create_engine, init_db, load_df)
  |     |-- config/settings.py
  |     |-- database/models.py    (RawAiNews, StagingAiNews)
  |     +-- utils/logger.py
  |-- processing/validator.py     (validate_articles)      [Week 2]
  |-- processing/transformer.py   (transform_articles)     [Week 2]
  |-- processing/scorer.py        (score_articles)         [Week 2]
  +-- utils/logger.py

dashboard/app.py                                           [Week 2]
  +-- analytics/queries.py        (10 analytics functions) [Week 2]
        +-- database/warehouse.py (engine creation)
```

---

## Data Flow — Column Mapping

### Raw Layer (raw_ai_news)

```
GNews API JSON          ->   raw_ai_news Table Column
------------------------------------------------------
article.title           ->   title
article.source.name     ->   source
article.author          ->   author  (default: "Unknown")
article.description     ->   description
article.publishedAt     ->   published_at  (parsed to TIMESTAMPTZ)
article.url             ->   url  (UNIQUE -- idempotency key)
[hardcoded "AI"]        ->   category
[auto by PostgreSQL]    ->   ingested_at  (server_default=now())
[auto-increment]        ->   id
```

### Staging Layer (stg_ai_news) — Week 2

```
raw_ai_news column      ->   stg_ai_news column        Transform Applied
-----------------------------------------------------------------------
title                   ->   title                     strip whitespace
source                  ->   source                    title-case
author                  ->   author                    "Unknown" if empty
description             ->   description               truncate to 1000 chars
published_at            ->   published_at              carried over
url                     ->   url                       strip whitespace
category                ->   category                  uppercase

[computed by scorer]    ->   intelligence_score        0-100 integer
[computed by scorer]    ->   score_category            "Hot Trend" etc.
[from validator]        ->   is_valid                  1 (all staged = valid)
[from validator]        ->   validation_notes          "" (empty = clean)
[computed by scorer]    ->   keywords_found            "openai, gpt, llm"
[auto by PostgreSQL]    ->   processed_at              server_default=now()
```

---

## Future Architecture (Weeks 3–5)

```
Week 1 (DONE): GNews API -> Python -> raw_ai_news
Week 2 (DONE): raw_ai_news -> Processing -> stg_ai_news -> Dashboard
Week 3:        Multiple APIs -> raw_ai_news -> stg_ -> fct_ (dbt)
Week 4:        [Week 3] + Scheduled ingestion (cron/Airflow)
Week 5:        [Week 4] + Docker + Cloud deployment
`
