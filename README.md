# AI Pulse — GenAI Industry Trends Warehouse

> **Automatically ingests AI news from public APIs, stores it in a PostgreSQL warehouse, and prepares clean datasets for analytics and dashboards.**

![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791?logo=postgresql)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0-red)
![Pandas](https://img.shields.io/badge/Pandas-2.1-150458?logo=pandas)
![License](https://img.shields.io/badge/License-MIT-green)
![Week](https://img.shields.io/badge/Week-1%20of%205-orange)

---

## 📌 Project Overview

**AI Pulse** is a Data Engineering portfolio project built during a 5-week internship (June–July 2026). It simulates real Junior Data Engineer work at a fictional startup that sells insights about the Generative AI industry.

The project evolves week-by-week from a simple API → PostgreSQL pipeline into a fully deployed, multi-source analytics system with dashboards, containerization, and production-grade practices.

**This repository is Week 1** — the foundation layer.

---

## 🚨 Business Problem

Analysts and researchers at AI Pulse currently spend **3–5 hours per day** manually browsing news websites to understand trends in the Generative AI space. This process is:

- **Inconsistent** — different analysts use different sources
- **Non-reproducible** — no historical data is saved for trend analysis
- **Slow** — analysis is always behind real-time events

**Solution:** Build a reusable data pipeline that automatically collects AI news every day, stores it in a structured warehouse, and makes it queryable by any analyst with SQL knowledge.

---

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                  AI PULSE — WEEK 1 PIPELINE                  │
└──────────────────────────────────────────────────────────────┘

  ┌──────────────┐     HTTP GET      ┌─────────────────────┐
  │  GNews API   │ ─────────────────▶│  ingestion/         │
  │  gnews.io    │  JSON Response    │  gnews_client.py    │
  └──────────────┘                   └──────────┬──────────┘
                                                │
                                      pd.DataFrame
                                                │
                                     ┌──────────▼──────────┐
                                     │  database/          │
                                     │  warehouse.py       │
                                     │  (SQLAlchemy ORM)   │
                                     └──────────┬──────────┘
                                                │
                                   INSERT ... ON CONFLICT
                                    DO NOTHING (upsert)
                                                │
                                     ┌──────────▼──────────┐
                                     │  PostgreSQL         │
                                     │  ai_pulse_db        │
                                     │  raw_ai_news        │
                                     └─────────────────────┘

  Cross-cutting: config/ + utils/logger.py + tests/
```

**Full architecture details:** → [`docs/architecture.md`](docs/architecture.md)

---

## 🛠️ Tech Stack

| Tool | Version | Purpose |
|---|---|---|
| **Python** | 3.11 | Core language for ingestion and transformation |
| **requests** | 2.31.0 | HTTP library for calling the GNews API |
| **pandas** | 2.1.4 | Transform JSON responses into DataFrames |
| **SQLAlchemy** | 2.0.25 | ORM — define tables as Python classes |
| **psycopg2-binary** | 2.9.9 | PostgreSQL connector (used by SQLAlchemy) |
| **python-dotenv** | 1.0.0 | Load `.env` secrets into environment variables |
| **PostgreSQL** | 16 | Data warehouse (raw storage layer) |
| **pytest** | 7.4.4 | Unit testing framework |

---

## 📁 Project Structure

```
ai-pulse-warehouse/
│
├── config/
│   ├── __init__.py            # Package marker
│   └── settings.py            # All config: API keys, DB URL, parameters
│
├── ingestion/
│   ├── __init__.py
│   └── gnews_client.py        # GNews API fetcher → returns pd.DataFrame
│
├── database/
│   ├── __init__.py
│   ├── models.py              # SQLAlchemy ORM model for raw_ai_news table
│   └── warehouse.py           # Engine, schema init, idempotent upsert
│
├── utils/
│   ├── __init__.py
│   └── logger.py              # Centralized logger (console + file)
│
├── tests/
│   ├── __init__.py
│   └── test_ingestion.py      # 10 unit tests for ingestion layer
│
├── docs/
│   ├── design_doc.md          # Full design document (7 sections)
│   ├── architecture.md        # Architecture diagram + data flow
│   └── status_week1.md        # Week 1 status one-pager
│
├── sql/
│   └── sample_queries.sql     # 7 analytical SQL queries
│
├── logs/
│   └── .gitkeep               # Placeholder — actual .log files are gitignored
│
├── .env.example               # Template for environment variables
├── .gitignore                 # Excludes secrets, venv, cache
├── main.py                    # Pipeline entry point — run this!
├── requirements.txt           # Pinned Python dependencies
└── README.md                  # This file
```

---

## ⚙️ Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL 16 (see installation below)
- Git

---

### Step 1: Install PostgreSQL

**Windows:**
1. Download the installer: https://www.postgresql.org/download/windows/
2. Run the installer. Accept defaults.
3. Set a password for user `postgres` (use `postgres` to match defaults)
4. Open **pgAdmin** (installed with PostgreSQL)
5. Create the database:
   - Right-click "Databases" → Create → Database
   - Name: `ai_pulse_db`
   - Owner: `postgres`
   - Save

**Alternative — using psql command line:**
```bash
psql -U postgres
CREATE DATABASE ai_pulse_db;
\q
```

---

### Step 2: Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/ai-pulse-warehouse.git
cd ai-pulse-warehouse
```

---

### Step 3: Set Up Python Virtual Environment

```bash
# Create a virtual environment named 'venv'
python -m venv venv

# Activate it (Windows PowerShell)
.\venv\Scripts\Activate.ps1

# Activate it (Windows CMD)
venv\Scripts\activate.bat

# Activate it (macOS/Linux)
source venv/bin/activate

# You should see (venv) at the start of your terminal prompt
```

---

### Step 4: Install Dependencies

```bash
pip install -r requirements.txt
```

---

### Step 5: Configure Environment Variables

```bash
# Copy the template
copy .env.example .env        # Windows
cp .env.example .env          # macOS/Linux

# Open .env in VS Code and fill in your values
code .env
```

Edit `.env`:
```env
# Get your free API key at: https://gnews.io (register, go to API key section)
GNEWS_API_KEY=your_actual_api_key_here

# Database connection (match what you set during PostgreSQL install)
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/ai_pulse_db
```

---

### Step 6: Run the Pipeline

```bash
python main.py
```

**Expected output:**
```
╔══════════════════════════════════════════════════════════════╗
║           AI PULSE — GenAI Industry Trends Warehouse         ║
║                   Data Pipeline — Week 1                     ║
║          GNews API → Python → Pandas → PostgreSQL           ║
╚══════════════════════════════════════════════════════════════╝

2026-06-24 18:30:01 | main | INFO     | Pipeline execution started
2026-06-24 18:30:01 | main | INFO     | STEP 1/5 — Validating configuration
2026-06-24 18:30:01 | main | INFO     | ✓ All required environment variables are present
2026-06-24 18:30:01 | main | INFO     | STEP 2/5 — Connecting to PostgreSQL
2026-06-24 18:30:02 | main | INFO     | Database connection test: PASSED ✓
2026-06-24 18:30:02 | main | INFO     | STEP 3/5 — Initializing database schema
2026-06-24 18:30:02 | main | INFO     | Table 'raw_ai_news' is ready
2026-06-24 18:30:02 | main | INFO     | STEP 4/5 — Fetching AI news from GNews API
2026-06-24 18:30:04 | main | INFO     | ✓ Fetched 10 articles from GNews API
2026-06-24 18:30:04 | main | INFO     | STEP 5/5 — Loading data into PostgreSQL warehouse
2026-06-24 18:30:04 | main | INFO     | ✓ Insert complete: 10 new records inserted, 0 duplicates skipped.

╔══════════════════════════════════════════════════════════════╗
║                    PIPELINE RUN SUMMARY                      ║
╠══════════════════════════════════════════════════════════════╣
║  Status:           SUCCESS ✓                                 ║
║  Run Duration:     3.24s                                     ║
║  Articles Fetched: 10                                        ║
║  New Records:      10                                        ║
║  Duplicates Skip:  0                                         ║
║  Total in DB:      10                                        ║
╚══════════════════════════════════════════════════════════════╝
```

---

### Step 7: Run Tests

```bash
# Run all tests with verbose output
pytest tests/ -v
```

**Expected output:**
```
tests/test_ingestion.py::TestFetchAiNews::test_returns_dataframe_on_success PASSED
tests/test_ingestion.py::TestFetchAiNews::test_dataframe_has_correct_columns PASSED
tests/test_ingestion.py::TestFetchAiNews::test_url_column_has_correct_values PASSED
tests/test_ingestion.py::TestFetchAiNews::test_category_is_always_ai PASSED
tests/test_ingestion.py::TestFetchAiNews::test_articles_without_url_are_skipped PASSED
tests/test_ingestion.py::TestFetchAiNews::test_returns_none_on_connection_error PASSED
tests/test_ingestion.py::TestFetchAiNews::test_returns_none_on_http_error PASSED
tests/test_ingestion.py::TestParseDatetime::test_parses_valid_iso_string PASSED
tests/test_ingestion.py::TestParseDatetime::test_returns_none_for_empty_string PASSED
tests/test_ingestion.py::TestParseDatetime::test_returns_none_for_none_input PASSED
tests/test_ingestion.py::TestParseDatetime::test_returns_none_for_invalid_format PASSED

11 passed in 0.42s
```

> Tests run WITHOUT an API key or database connection — they use mocking.

---

### Step 8: Query the Data

Open **pgAdmin** or **psql** and run queries from `sql/sample_queries.sql`:

```sql
-- Total articles in the warehouse
SELECT COUNT(*) AS total_articles FROM raw_ai_news;

-- Latest 10 articles
SELECT title, source, published_at FROM raw_ai_news ORDER BY published_at DESC LIMIT 10;

-- Top sources by article count
SELECT source, COUNT(*) AS count FROM raw_ai_news GROUP BY source ORDER BY count DESC;

-- Articles per day
SELECT DATE(published_at) AS day, COUNT(*) AS articles FROM raw_ai_news GROUP BY day ORDER BY day DESC;
```

---

## 🗄️ Database Schema

```sql
Table: raw_ai_news
┌────────────────┬──────────────────────────────────────────────────────┐
│ Column         │ Type                  │ Notes                        │
├────────────────┼───────────────────────┼──────────────────────────────┤
│ id             │ SERIAL PRIMARY KEY    │ Auto-increment               │
│ title          │ TEXT NOT NULL         │ Article headline             │
│ source         │ TEXT                  │ News source name             │
│ author         │ TEXT                  │ Author (default: "Unknown")  │
│ description    │ TEXT                  │ Article subtitle             │
│ published_at   │ TIMESTAMPTZ           │ When published (UTC)         │
│ url            │ TEXT UNIQUE NOT NULL  │ Idempotency key              │
│ category       │ VARCHAR(50)           │ "AI" for all Week 1 records  │
│ ingested_at    │ TIMESTAMPTZ DEFAULT   │ When WE loaded this record   │
│                │ NOW()                 │                              │
└────────────────┴───────────────────────┴──────────────────────────────┘
```

---

## 📊 Data Sources

| Source | API | Free Tier | Coverage |
|---|---|---|---|
| **GNews** (Week 1) | `gnews.io/api/v4/search` | 100 req/day, 10 articles/req | 60,000+ news sources |
| Reddit (Week 3) | Reddit API | Generous free tier | r/MachineLearning, r/artificial |
| Hacker News (Week 3) | `hacker-news.firebaseio.com` | Unlimited | Tech/startup news |

---

## 🗺️ Roadmap

| Week | Theme | Key Additions |
|---|---|---|
| **Week 1** *(current)* | Foundation | GNews → PostgreSQL raw layer |
| **Week 2** | Core Build | dbt transformations, ADRs, staging + mart tables |
| **Week 3** | Extension | Reddit/HN ingestion, data quality tests |
| **Week 4** | Deploy | Streamlit dashboard, Docker, live URL |
| **Week 5** | Showcase | Loom video, reflection, resume bullets |

---

## 📝 Week 1 Key Learnings

1. **APIs are just HTTP requests** — `requests.get(url, params={"apikey": ...})`
2. **Environment variables > hardcoding** — never put secrets in code
3. **Idempotency is critical in DE** — `ON CONFLICT DO NOTHING` prevents duplicates
4. **ORM abstracts SQL** — define tables as Python classes, SQLAlchemy writes the SQL
5. **Logging > printing** — timestamps, levels, and file output for production code
6. **Unit tests with mocking** — test without real APIs or databases
7. **Data Engineering naming conventions** — `raw_` → `stg_` → `fct_`
8. **Separation of concerns** — each module has one job

---

## 🔧 Troubleshooting

| Error | Cause | Fix |
|---|---|---|
| `Missing required environment variables` | `.env` file missing or `GNEWS_API_KEY` not set | Copy `.env.example` to `.env` and fill values |
| `Cannot connect to PostgreSQL` | PostgreSQL not running | Start PostgreSQL service in Windows Services |
| `Database "ai_pulse_db" does not exist` | DB not created | Run `CREATE DATABASE ai_pulse_db;` in psql |
| `401 Unauthorized from GNews API` | Invalid API key | Check key at gnews.io → Dashboard |
| `429 Too Many Requests` | Free tier limit hit | Wait until midnight UTC for reset |

---

## 📜 License

MIT License — free to use, modify, and distribute.

---

## 🙏 Acknowledgements

- **GNews API** — gnews.io — for providing free AI news data
- **SQLAlchemy** — for making database work pythonic
- **Faculty & Mentors** — for the structured internship framework
- Built as part of **H1 — APIs to Warehouse**, Foundations of Data Engineering Internship (June–July 2026)
