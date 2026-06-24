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

PostgreSQL: raw_ai_news table
```

---

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
