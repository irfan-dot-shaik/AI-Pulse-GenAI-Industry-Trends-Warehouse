# Design Document — AI Pulse: GenAI Industry Trends Warehouse

**Document Version:** 1.0
**Author:** Junior Data Engineer, AI Pulse
**Date:** June 24, 2026
**Week:** 1 — Foundation + Architecture
**Status:** Active

---

## 1. Problem Statement

Analysts and researchers at AI Pulse currently spend **3–5 hours daily** manually browsing news websites, Twitter/X, LinkedIn, and newsletters to understand what is happening in the Generative AI ecosystem.

This manual process has three critical problems:

| Problem | Impact |
|---|---|
| **Inconsistency** | Different analysts check different sources, creating information silos |
| **Latency** | News collected manually is hours behind real-time |
| **Non-reproducible** | No historical data is kept — trends cannot be analyzed over time |

The engineering goal is to replace this manual process with an automated, repeatable data pipeline.

---

## 2. Business Scenario

**Company:** AI Pulse (fictional startup)
**Industry:** AI/ML Insights and Analytics
**Team:** Data Engineering

**My Role:** Junior Data Engineer
**Task from CTO:** *"Build a reusable pipeline that pulls AI news from public APIs, stores it in our warehouse, and makes it available for analysts and dashboards."*

**Stakeholders:**
- **Analysts**: Want clean, queryable data in SQL
- **Researchers**: Want historical trend data (30+ days)
- **Executives**: Want a dashboard showing AI industry movement (Week 4)

**Success Criteria for Week 1:**
- [ ] Data automatically flows from GNews API to PostgreSQL
- [ ] No duplicate records regardless of how many times pipeline runs
- [ ] Every run is logged and traceable
- [ ] Any developer can clone the repo and run the pipeline in < 20 minutes

---

## 3. Architecture

### 3.1 Week 1 Architecture (Current)

```
┌─────────────────────────────────────────────────────────┐
│                   EXTERNAL WORLD                        │
│                                                         │
│    ┌───────────────────────────────┐                    │
│    │        GNews API              │                    │
│    │  https://gnews.io/api/v4/     │                    │
│    │  • 100 req/day (free tier)    │                    │
│    │  • Returns JSON               │                    │
│    │  • AI/GenAI news articles     │                    │
│    └───────────────┬───────────────┘                    │
└───────────────────┼─────────────────────────────────────┘
                    │ HTTP GET (requests)
                    ↓
┌───────────────────────────────────────────────────────────┐
│                 PYTHON PIPELINE (local)                   │
│                                                           │
│  ┌──────────────────────────────────────────────────┐    │
│  │              ingestion/gnews_client.py           │    │
│  │  • Fetch JSON from GNews API                     │    │
│  │  • Validate HTTP response                        │    │
│  │  • Parse & flatten JSON structure                │    │
│  │  • Handle errors gracefully                      │    │
│  │  • Return pd.DataFrame                           │    │
│  └────────────────────┬─────────────────────────────┘    │
│                       │ pd.DataFrame                      │
│  ┌────────────────────▼─────────────────────────────┐    │
│  │              database/warehouse.py               │    │
│  │  • SQLAlchemy engine (connection pool)           │    │
│  │  • INSERT ... ON CONFLICT DO NOTHING             │    │
│  │  • Idempotent: safe to run multiple times        │    │
│  └────────────────────┬─────────────────────────────┘    │
│                       │ SQL INSERT                        │
└───────────────────────┼───────────────────────────────────┘
                        ↓
┌───────────────────────────────────────────────────────────┐
│               POSTGRESQL WAREHOUSE                        │
│                                                           │
│  Database: ai_pulse_db                                    │
│  Table: raw_ai_news                                       │
│  Layer: RAW (no transformations)                          │
│                                                           │
│  ┌─────────────────────────────────────────────────┐     │
│  │ id │ title │ source │ author │ published_at │ …  │     │
│  ├────┼───────┼────────┼────────┼──────────────┼───┤     │
│  │  1 │ GPT-5 │ TC     │ Unknwn │ 2026-06-24   │ … │     │
│  │  2 │ Gemini│ Wired  │ Unknwn │ 2026-06-23   │ … │     │
│  └─────────────────────────────────────────────────┘     │
└───────────────────────────────────────────────────────────┘
```

### 3.2 Data Flow

```
GNews API (JSON)
    ↓
gnews_client.fetch_ai_news()
    ├── Validate API key & response
    ├── Parse article list
    ├── Flatten nested JSON (source.name → source)
    ├── Add ingested_at = datetime.now(UTC)
    └── Return pd.DataFrame

pd.DataFrame
    ↓
warehouse.load_dataframe_to_warehouse()
    ├── Convert DataFrame → list of dicts
    ├── Build INSERT ... ON CONFLICT DO NOTHING
    ├── Execute in SQLAlchemy session
    ├── Commit transaction
    └── Return count of new rows inserted

PostgreSQL: raw_ai_news table (RAW LAYER - never modified)

-- WEEK 2 ADDITION: Processing Pipeline --

pd.DataFrame (same articles, from memory)
    |
    v
validator.validate_articles()
    |-- RULE 1: title not empty or placeholder
    |-- RULE 2: title >= 10 characters
    |-- RULE 3: url not empty
    |-- RULE 4: url starts with 'http'
    +-- RULE 5: published_at not null
    Returns: valid_df (passes all), invalid_df (fails any), report

valid_df
    |
    v
transformer.transform_articles()
    |-- strip whitespace from all text fields
    |-- title-case source names
    |-- normalize author ("Unknown" if blank)
    |-- truncate description to 1000 chars
    |-- uppercase category
    +-- add is_valid=True, validation_notes=""
    Returns: clean_df with 2 new metadata columns

clean_df
    |
    v
scorer.score_articles()
    |-- Recency score:     0-30 pts (how recent is it?)
    |-- Keyword score:     0-40 pts (AI keywords in title+description?)
    |-- Credibility score: 0-20 pts (is source trusted?)
    +-- Length score:      0-10 pts (is description detailed?)
    Returns: scored_df with intelligence_score, score_category, keywords_found

scored_df
    |
    v
warehouse.load_staging_to_warehouse()
    |-- Column filter (only stg_ai_news columns)
    |-- bool -> int conversion (is_valid)
    |-- NaN/NaT -> None cleanup
    +-- INSERT INTO stg_ai_news ... ON CONFLICT (url) DO NOTHING

PostgreSQL: stg_ai_news table (STAGING LAYER - queryable by analytics)
```

### 3.3 Warehouse Layer Philosophy (Week 2)

**Why two tables instead of one?**

| Layer | Table | Purpose | Modified? |
|---|---|---|---|
| Raw | `raw_ai_news` | Permanent audit trail, exact API data | Never |
| Staging | `stg_ai_news` | Clean, scored, analytics-ready | Re-derived from raw |

**The Immutability Principle:**
Raw data is sacred. Once written, it is never changed. If processing logic
improves, we re-run processing FROM the raw table — not from the API.
This gives us historical coverage, API quota savings, and full auditability.



## 4. Database Schema

### Table: `raw_ai_news`

```sql
CREATE TABLE raw_ai_news (
    id           SERIAL PRIMARY KEY,
    title        TEXT NOT NULL,
    source       TEXT,
    author       TEXT,
    description  TEXT,
    published_at TIMESTAMP WITH TIME ZONE,
    url          TEXT NOT NULL UNIQUE,    -- Idempotency key
    category     VARCHAR(50) DEFAULT 'AI',
    ingested_at  TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

**Design Decisions:**

| Column | Decision | Reason |
|---|---|---|
| `url` | `UNIQUE NOT NULL` | Prevents duplicate articles; idempotency key |
| `published_at` | `TIMESTAMPTZ` | Timezone-aware; supports global sources |
| `ingested_at` | `DEFAULT NOW()` | Set by PostgreSQL, not Python; more reliable |
| `category` | `VARCHAR(50)` | Short, fixed values; TEXT is overkill |
| `author` | Nullable | GNews rarely provides author data |
| `id` | `SERIAL` | Auto-increment; we never set it manually |

---

## 4.5 Entity Relationship Diagram (ER Diagram)

### What is an ER Diagram?

An ER Diagram shows:
- What **tables** exist in the database
- What **columns** each table has
- What **constraints** are enforced (PRIMARY KEY, UNIQUE, NOT NULL)
- How tables **relate** to each other

---

### ASCII ER Diagram

```
+------------------------------------------------------------------+
|                       EXTERNAL WORLD                             |
|                                                                  |
|   GNews API (gnews.io)                                           |
|   Returns JSON:  title, source, description, url, publishedAt    |
+----------------------------+-------------------------------------+
                             |
                             | HTTP GET (100 req/day free tier)
                             | ingestion/gnews_client.py
                             v
+------------------------------------------------------------------+
|               TABLE: raw_ai_news  (RAW LAYER)                    |
|------------------------------------------------------------------|
| PK  id            SERIAL         NOT NULL  auto-increment        |
|     title         TEXT           NOT NULL                        |
|     source        TEXT           NULLABLE                        |
|     author        TEXT           NULLABLE                        |
|     description   TEXT           NULLABLE                        |
|     published_at  TIMESTAMPTZ    NULLABLE                        |
| UQ  url           TEXT           NOT NULL  <-- UNIQUE KEY        |
|     category      VARCHAR(50)    DEFAULT 'AI'                    |
|     ingested_at   TIMESTAMPTZ    DEFAULT NOW() (set by Postgres) |
|------------------------------------------------------------------|
| CONSTRAINTS:                                                     |
|   PRIMARY KEY:  id                                               |
|   UNIQUE:       url  (named: uq_raw_ai_news_url)                 |
+--------------------------------+---------------------------------+
                                 |
                                 | Processing Pipeline (Week 2)
                                 |   validator.py  -> validate
                                 |   transformer.py -> normalize
                                 |   scorer.py     -> score 0-100
                                 v
+------------------------------------------------------------------+
|               TABLE: stg_ai_news  (STAGING LAYER)                |
|------------------------------------------------------------------|
| PK  id                SERIAL       NOT NULL  auto-increment      |
|     title             TEXT         NOT NULL  (cleaned)           |
|     source            TEXT         NULLABLE  (title-cased)       |
|     author            TEXT         NULLABLE  ("Unknown" default)  |
|     description       TEXT         NULLABLE  (max 1000 chars)    |
|     published_at      TIMESTAMPTZ  NULLABLE  (carried over)      |
| UQ  url               TEXT         NOT NULL  <-- UNIQUE KEY      |
|     category          VARCHAR(50)  DEFAULT 'AI' (uppercase)      |
|     ingested_at       TIMESTAMPTZ  NULLABLE  (from raw)          |
|     intelligence_score INTEGER     DEFAULT 0  (0-100 score)      |
|     score_category    VARCHAR(50)  DEFAULT 'Normal'              |
|     is_valid          INTEGER      DEFAULT 1  (1=True, 0=False)  |
|     validation_notes  TEXT         DEFAULT ''                    |
|     keywords_found    TEXT         DEFAULT ''                    |
|     processed_at      TIMESTAMPTZ  DEFAULT NOW() (set by Postgres)|
|------------------------------------------------------------------|
| CONSTRAINTS:                                                     |
|   PRIMARY KEY:  id                                               |
|   UNIQUE:       url  (named: uq_stg_ai_news_url)                 |
+--------------------------------+---------------------------------+
                                 |
                                 | analytics/queries.py
                                 | (10 Python functions wrapping SQL)
                                 v
+------------------------------------------------------------------+
|           ANALYTICS LAYER  (dashboard reads from HERE)           |
|                                                                  |
|   dashboard/app.py        <- Home page KPI cards                 |
|   dashboard/pages/        <- Explorer, Analytics, Top News       |
|   analytics/queries.py    <- All SQL runs against stg_ai_news    |
+------------------------------------------------------------------+
```

---

### Primary Keys

```
raw_ai_news.id     SERIAL PRIMARY KEY
  - Auto-increments: 1, 2, 3, 4, ...
  - Set by PostgreSQL automatically
  - You NEVER insert the id value manually
  - Uniquely identifies every row in raw_ai_news

stg_ai_news.id     SERIAL PRIMARY KEY
  - Same pattern, independent sequence
  - The id in stg_ai_news is NOT the same as raw_ai_news id
  - Each table manages its own id sequence
```

---

### Unique Constraints

```
raw_ai_news:   UNIQUE(url)   [named: uq_raw_ai_news_url]
stg_ai_news:   UNIQUE(url)   [named: uq_stg_ai_news_url]
```

Both tables enforce `url` uniqueness independently.
This allows the `ON CONFLICT DO NOTHING` pattern in both tables.

---

### Why is URL the UNIQUE Key? (Not Title or ID)

This is one of the most important design decisions in the project.

| Option | Problem |
|---|---|
| `UNIQUE(title)` | Two articles from different sources can have identical titles |
| `UNIQUE(id from API)` | GNews does not return a stable unique article ID |
| `UNIQUE(url)` | Every article has exactly one canonical URL — never duplicated |

**The URL is the natural business key for a news article.**

Example:
- `https://techcrunch.com/2026/07/01/openai-gpt5/` → always identifies one specific article
- If the pipeline runs 100 times, this URL appears exactly once in the DB
- `ON CONFLICT (url) DO NOTHING` → the 2nd–100th run silently skips it

This property is called **idempotency**: running the pipeline multiple times
produces the same result as running it once. This is a core Data Engineering principle.

---

### How Raw and Staging Tables Are Related

```
raw_ai_news  ←──────────────────────────────── stg_ai_news
     |                                               |
     |  LOGICAL RELATIONSHIP (not a foreign key)     |
     |                                               |
     |  Same article appears in both tables          |
     |  linked by the URL column                     |
     |                                               |
     |  raw_ai_news.url == stg_ai_news.url           |
```

**Key design decision:** There is NO foreign key between the two tables.

**Why not use a foreign key?**

In traditional relational databases, you would add:
```sql
-- We deliberately chose NOT to do this:
stg_ai_news.raw_id INTEGER REFERENCES raw_ai_news(id)
```

**Reasons we don't:**

1. **Re-derivability** — We want to be able to `TRUNCATE stg_ai_news` and
   rebuild it from raw without any FK cascade complications.

2. **Independence** — The staging table should be able to receive data from
   MULTIPLE raw sources in the future (not just raw_ai_news).

3. **Data Engineering norm** — In real warehouse tools like dbt, Snowflake,
   or BigQuery, staging tables are logically related but not FK-constrained.
   The URL is the shared key used for joining when needed.

**When you need to join them:**
```sql
-- Join to compare raw vs. cleaned version of an article:
SELECT
    r.title          AS raw_title,
    s.title          AS clean_title,
    r.source         AS raw_source,
    s.source         AS clean_source,
    s.intelligence_score
FROM raw_ai_news r
JOIN stg_ai_news s ON r.url = s.url;
```

---

### Which Table Does the Dashboard Read From?

```
+-----------------+     Dashboard reads?     +-------------------+
|  raw_ai_news    |   NO  (audit trail only)  |  stg_ai_news      |
|                 |                           |                   |
|  id, title,     |                           |  id, title,       |
|  source, url,   |                           |  source, url,     |
|  published_at,  |                           |  intelligence_score|
|  ingested_at    |                           |  score_category,  |
|                 |                           |  keywords_found,  |
|                 |                           |  processed_at     |
+-----------------+                           +-------------------+
                                                       ^
                                                       |
                                              analytics/queries.py
                                              (all 10 functions)
                                                       |
                                                dashboard/app.py
```

**Rule:** The dashboard ALWAYS queries `stg_ai_news`.
- It is clean (whitespace stripped, authors normalized)
- It is scored (every article has intelligence_score 0-100)
- It is validated (only articles that passed all 5 rules)

The `raw_ai_news` table exists purely as an immutable audit trail.
In a production system, only Data Engineers and DBAs access raw tables directly.

---

## 5. Tech Stack Decisions

### Why Python 3.11?
- Industry standard for Data Engineering
- Rich ecosystem: pandas, SQLAlchemy, requests
- 3.11 brings ~25% performance improvement over 3.10
- Long-term support (LTS) until 2027

### Why GNews API?
- Free tier (100 req/day) — perfect for Week 1
- Returns structured JSON — minimal parsing effort
- Covers 60,000+ news sources in 60+ languages
- Relevance ranking built-in
- **Limitation:** No author field — defaults to "Unknown"

### Why PostgreSQL?
- Free, open-source, production-grade
- ACID compliant (transactions are safe)
- Native support for `ON CONFLICT DO NOTHING` (upsert)
- `TIMESTAMP WITH TIME ZONE` for global pipelines
- Used at: Amazon, Instagram, Shopify, Airbnb
- Same stack used in most DE job interviews

### Why SQLAlchemy (ORM)?
- Database-agnostic: switch from PostgreSQL to BigQuery by changing one URL
- No SQL injection risk (parameters are auto-sanitized)
- Python-native: define tables as classes
- `create_all(checkfirst=True)` handles schema creation safely

### Why pandas?
- Industry standard for batch data transformation
- Easy JSON-to-DataFrame conversion
- Built-in data inspection (`df.head()`, `df.describe()`)
- **Limitation:** Loads all data into memory (acceptable for Week 1 volumes)

### Why python-dotenv?
- Keeps secrets out of code
- Works identically in development and CI/CD
- Zero-configuration secret management

---

## 6. Engineering Principles Applied

### Idempotency
Running the pipeline 10 times produces the same result as running it once.
**Implementation:** `INSERT ... ON CONFLICT (url) DO NOTHING`

### Fail Fast
If configuration is missing (no API key), the pipeline crashes immediately with a clear error message instead of failing mysteriously 30 seconds in.
**Implementation:** `validate_config()` runs at startup

### Separation of Concerns
Each module has one responsibility:
- `config/` → configuration only
- `ingestion/` → API fetching only
- `database/` → database operations only
- `utils/` → shared utilities only
- `main.py` → orchestration only

### Observability
Every significant action is logged with a timestamp and log level. Log files persist on disk. A pipeline failure can be diagnosed by reading the log file.

### No Secrets in Code
All credentials live in `.env` (which is in `.gitignore`). `.env.example` serves as documentation.

---

## 7. Future Roadmap

### Week 2 — Core Build + SQL Transformations

**Theme:** Make the pipeline fully functional end-to-end.

- Add `dbt` project for SQL transformations
- Create staging model: `stg_ai_news` (clean, standardized)
- Create mart model: `fct_ai_articles` (analytical-ready)
- Write Architecture Decision Records (ADRs)
- Add retry mechanism for failed API calls

**Architecture:**
```
GNews API → Python → raw_ai_news → dbt → stg_ai_news → fct_ai_articles
```

### Week 3 — Multi-Source Ingestion + Polish

**Theme:** Show you can generalize pipelines.

- Add second data source: Reddit API (`/r/MachineLearning`, `/r/artificial`)
- Both sources land in the same `raw_ai_news` table (different `category` values)
- Extend dbt models to handle multi-source data
- Add data quality tests (dbt tests + Great Expectations)
- Improve README so a friend can clone-and-run in < 20 minutes

**Architecture:**
```
GNews API  ↘
Reddit API  → Python → PostgreSQL → dbt → Analytics
```

### Week 4 — Analytics Dashboard + Deployment

**Theme:** Make insights visible.

- Build Streamlit dashboard showing:
  - Articles per day (line chart)
  - Top sources (bar chart)
  - Company mentions (OpenAI, Google, Anthropic)
  - Keyword search
- Containerize with Docker Compose
- Deploy to a free cloud platform (Render / Railway)

**Architecture:**
```
[Week 3] + Streamlit Dashboard + Docker
```

### Week 5 — Final Submission + Showcase

**Theme:** Polish, reflect, present.

- Record 3-minute Loom walkthrough
- Finalize all 3 ADRs
- Write 1000–1500 word reflection piece
- Update resume with 2–3 impact bullets
- Prepare showcase slide

### 3rd Year Extension Path

```
Current (Week 1):       Batch pipeline, manual run
↓
3rd Year Semester 1:    Airflow scheduling, dbt lineage
↓
3rd Year Semester 2:    Kafka streaming ingestion
↓
3rd Year Internship:    Data contracts, Great Expectations
↓
Final Year Project:     Production-grade, feature store
```

**Target Roles After This Project:**
- Data Engineer (Entry Level)
- Analytics Engineer
- Junior Data Engineer at startups and MNCs

---

*Document maintained by the AI Pulse Data Engineering team.*
*Last updated: June 24, 2026*
