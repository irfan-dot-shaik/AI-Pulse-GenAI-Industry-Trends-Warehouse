# AI Pulse — Week 1 Architecture Reference

## System Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                    AI PULSE — WEEK 1 ARCHITECTURE                    │
│               GNews API → Python → Pandas → PostgreSQL               │
└──────────────────────────────────────────────────────────────────────┘

  ┌─────────────────────┐
  │     DATA SOURCE      │
  │                      │
  │   GNews API          │   ← External REST API (HTTP/HTTPS)
  │   gnews.io           │     Returns JSON with AI news articles
  │   Free Tier: 100     │     100 requests/day on free plan
  │   req/day            │
  └──────────┬───────────┘
             │
             │  HTTP GET Request
             │  (requests library)
             ↓
  ┌─────────────────────┐
  │   INGESTION LAYER   │
  │                      │
  │  ingestion/          │   ← Responsible for fetching data only
  │    gnews_client.py   │     Error handling + retry logic
  │                      │     Returns pd.DataFrame
  └──────────┬───────────┘
             │
             │  JSON → Pandas DataFrame
             │  (pandas library)
             ↓
  ┌─────────────────────┐
  │  TRANSFORMATION     │
  │  (Light, Week 1)    │
  │                      │   ← Flatten nested JSON structure
  │  • Extract fields    │     Parse ISO8601 datetime strings
  │  • Add ingested_at   │     Add ingested_at timestamp
  │  • Tag category      │     Tag category = "AI"
  │  • Skip no-URL rows  │     Skip invalid records
  └──────────┬───────────┘
             │
             │  Pandas DataFrame
             │
             ↓
  ┌─────────────────────┐
  │   DATABASE LAYER    │
  │                      │
  │  database/           │   ← ORM-based database operations
  │    models.py         │     SQLAlchemy table definition
  │    warehouse.py      │     Connection, insert, upsert logic
  └──────────┬───────────┘
             │
             │  INSERT ... ON CONFLICT DO NOTHING
             │  (idempotent upsert)
             ↓
  ┌─────────────────────┐
  │   POSTGRESQL        │
  │   WAREHOUSE         │
  │                      │   ← Raw data storage layer
  │  Database:           │     Table: raw_ai_news
  │    ai_pulse_db       │     Columns: id, title, source,
  │                      │       author, description,
  │  Table:              │       published_at, url,
  │    raw_ai_news       │       category, ingested_at
  └─────────────────────┘


  CROSS-CUTTING CONCERNS (Applied Everywhere)
  ┌────────────────────────────────────────────────────────┐
  │                                                        │
  │  config/settings.py  ← Single source of config truth  │
  │  utils/logger.py     ← Centralized logging (no print) │
  │  tests/              ← Unit tests (no API needed)      │
  │  .env                ← All secrets (never committed)   │
  │                                                        │
  └────────────────────────────────────────────────────────┘
```

## Module Dependency Graph

```
main.py
  ├── config/settings.py          (validate_config)
  ├── ingestion/gnews_client.py   (fetch_ai_news)
  │     ├── config/settings.py
  │     └── utils/logger.py
  ├── database/warehouse.py       (create_engine, init_db, load_df)
  │     ├── config/settings.py
  │     ├── database/models.py
  │     └── utils/logger.py
  └── utils/logger.py
```

## Data Flow — Column Mapping

```
GNews API JSON          →   raw_ai_news Table Column
───────────────────────────────────────────────────
article.title           →   title
article.source.name     →   source
article.author          →   author  (default: "Unknown")
article.description     →   description
article.publishedAt     →   published_at  (parsed to TIMESTAMPTZ)
article.url             →   url  (UNIQUE — idempotency key)
[hardcoded "AI"]        →   category
[datetime.now(UTC)]     →   ingested_at
[auto-increment]        →   id
```

## Future Architecture (Weeks 2–5)

```
Week 1 (NOW):
  GNews API → Python → PostgreSQL (raw_)

Week 2:
  GNews API → Python → PostgreSQL (raw_) → dbt (stg_ → fct_)

Week 3:
  GNews API  ↘
  Reddit API  → Python → PostgreSQL → dbt → Analytics
  HN API     ↗

Week 4:
  [Week 3] + Streamlit Dashboard

Week 5:
  [Week 4] + Docker Compose + Deployment
```
