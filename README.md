# AI Pulse — GenAI Industry Trends Warehouse

> **Automatically ingests AI news from multiple public APIs, stores it in a PostgreSQL warehouse, validates and transforms it, scores it with a proprietary Intelligence Score, and serves it through a production-ready Streamlit analytics dashboard.**

![Python](https://img.shields.io/badge/Python-3.12-blue?logo=python)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791?logo=postgresql)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0-red)
![Pandas](https://img.shields.io/badge/Pandas-2.1-150458?logo=pandas)
![Streamlit](https://img.shields.io/badge/Streamlit-1.57+-FF4B4B?logo=streamlit)
![Plotly](https://img.shields.io/badge/Plotly-6.5-3f4f75?logo=plotly)
![PRAW](https://img.shields.io/badge/PRAW-7.7.1-FF4500?logo=reddit)
![Tests](https://img.shields.io/badge/Tests-30%20passing-brightgreen)
![License](https://img.shields.io/badge/License-MIT-green)
![Week](https://img.shields.io/badge/Week-3%20of%205-orange)

---

## 📌 Project Overview

**AI Pulse** is a Data Engineering portfolio project built during a 5-week internship (June–July 2026). It simulates real Junior Data Engineer work at a fictional startup that sells insights about the Generative AI industry.

The project evolves week-by-week from a simple API → PostgreSQL pipeline into a fully deployed, multi-source analytics system with dashboards, containerization, and production-grade practices.

**This repository represents Week 3** — Multi-Source Ingestion. Building on the Week 2 processing and analytics UI layer, we have extended the pipeline with two additional data sources (Hacker News and Reddit), added a dedicated Source Analytics dashboard page, and expanded the test suite to 30 passing tests.

---

## 🚨 Business Problem

Analysts and researchers at AI Pulse currently spend **3–5 hours per day** manually browsing news websites to understand trends in the Generative AI space. This process is:

- **Inconsistent** — different analysts use different sources
- **Non-reproducible** — no historical data is saved for trend analysis
- **Slow** — analysis is always behind real-time events
- **Narrow** — relying on a single source misses community-driven insights

**Solution:** Build a reusable multi-source data pipeline that automatically collects AI news every day from GNews, Hacker News, and Reddit, stores it in a structured warehouse, assigns an *AI Intelligence Score* to filter out noise, and presents actionable insights through a premium financial-style Executive Dashboard.

---

## ✨ Features

### Week 1 — Foundation
- **GNews Ingestion Pipeline:** Automated ingestion of AI news into a structured Raw layer (`raw_ai_news`).
- **PostgreSQL Data Warehouse:** Two-layer schema following Medallion Architecture principles.

### Week 2 — Processing & Analytics UI
- **Data Validation & Transformation:** Pandas-based pipeline steps to clean titles, normalize publisher names, and filter out low-quality articles.
- **AI Intelligence Scoring:** Custom heuristic algorithm (0–100) based on keyword density, source reputation, recency, and content depth.
- **SQL Analytics Layer:** Reusable analytical query functions.
- **Interactive Streamlit Dashboard:** Multi-page, premium UI:
  - **Overview:** System status and pipeline health.
  - **News Explorer:** Advanced search, filtering, and pagination.
  - **Analytics:** Source distribution, trend charts, keyword frequency, score histogram.
  - **Top AI News:** Curated feed of the highest-scoring articles.
  - **Insights:** Dynamic executive KPIs and data quality metrics.

### Week 3 — Multi-Source Ingestion *(New)*
- **Hacker News Client:** Fetches AI-relevant stories from three HN feeds (top/best/new) merged and deduplicated. No API key required.
- **Reddit Client:** Fetches hot posts from `r/MachineLearning`, `r/artificial`, and `r/singularity` via PRAW. Credentials are optional — pipeline runs without them.
- **Multi-Source Pipeline:** `main.py` orchestrates all three sources into a single merged DataFrame fed into the **unchanged** processing and staging layer.
- **Source Analytics Page:** New dashboard page (`05_Source_Analytics.py`) with:
  - Executive summary cards (active sources, total articles, top source, best avg score)
  - Source contribution donut chart + horizontal bar
  - Average and max intelligence score comparison per source
  - Publication trends by source (multi-line chart)
  - Top keywords per source (faceted bar charts)
  - Source ranking table with article counts and score metrics
- **Expanded Test Suite:** 30 total passing tests (up from 11) covering the HN client, Reddit client, validator, transformer, and scorer.

---

## 🏗️ Architecture

```text
┌─────────────────────────────────────────────────────────────────────────┐
│                     AI PULSE — WEEK 3 ARCHITECTURE                      │
└─────────────────────────────────────────────────────────────────────────┘

  ┌──────────────┐
  │  GNews API   │ ──────────────────────────────────────┐
  └──────────────┘   HTTP GET (GNEWS_API_KEY required)   │
                                                         │
  ┌──────────────┐                                       ▼
  │  HackerNews  │ ─── Firebase REST (no auth) ──▶  ingestion/
  └──────────────┘    top + best + new feeds          gnews_client.py
                      merged, keyword-filtered         hn_client.py
  ┌──────────────┐                                    reddit_client.py
  │  Reddit API  │ ─── PRAW (optional creds)  ──▶       │
  └──────────────┘    r/MachineLearning                  │
                      r/artificial                pd.concat() merge
                      r/singularity                       │
                                                         ▼
                                              ┌─────────────────────┐
                                              │  raw_ai_news        │ Raw Layer
                                              │  (append + upsert)  │
                                              └──────────┬──────────┘
                                                         │
                                              ┌──────────▼──────────┐
                                              │  processing/        │
                                              │  validator.py       │ (5 rules)
                                              │  transformer.py     │ (6 steps)
                                              │  scorer.py          │ (0–100 score)
                                              └──────────┬──────────┘
                                                         │
                                              ┌──────────▼──────────┐
                                              │  stg_ai_news        │ Staging Layer
                                              │  (clean + scored)   │
                                              └──────────┬──────────┘
                                                         │
                                              ┌──────────▼──────────┐
                                              │  analytics/         │
                                              │  queries.py         │ 23+ functions
                                              └──────────┬──────────┘
                                                         │
                                              ┌──────────▼──────────┐
                                              │  dashboard/         │ Streamlit App
                                              │  Overview           │
                                              │  News Explorer      │
                                              │  Analytics          │
                                              │  Top AI News        │
                                              │  Insights           │
                                              │  Source Analytics   │ ← Week 3
                                              └─────────────────────┘
```

---

## 🛠️ Tech Stack

| Tool | Version | Purpose |
|---|---|---|
| **Python** | 3.12 | Core language for ingestion and transformation |
| **requests** | 2.31.0 | HTTP library for GNews and Hacker News APIs |
| **praw** | 7.7.1 | Python Reddit API Wrapper — Reddit ingestion *(Week 3)* |
| **pandas** | 2.1.4 | Transform JSON responses into DataFrames and clean data |
| **SQLAlchemy** | 2.0.25 | ORM — define tables as Python classes |
| **psycopg2-binary** | 2.9.9 | PostgreSQL connector (used by SQLAlchemy) |
| **PostgreSQL** | 16 | Data warehouse (raw and staging storage layer) |
| **Streamlit** | 1.57.0 | Interactive web dashboard framework |
| **Plotly** | 6.5.0 | Advanced interactive data visualization |
| **pytest** | 9.1.1 | Unit testing framework (30 passing tests) |
| **python-dotenv** | 1.0.0 | Load `.env` secrets into environment variables |

---

## 📊 Data Sources

| Source | Type | Auth Required | Articles/Run | Filter |
|---|---|---|---|---|
| **GNews API** | Editorial News | Yes (`GNEWS_API_KEY`) | Up to 10 | Search query |
| **Hacker News** | Community aggregator | **No** | Up to 10 | AI keyword filter |
| **Reddit** | Community discussion | Optional (PRAW) | Up to 30 | External links only |

---

## 📁 Project Structure

```text
ai-pulse-warehouse/
│
├── config/            # Centralized settings & environment variables
├── database/          # SQLAlchemy models & warehouse engine logic
├── ingestion/         # API clients
│   ├── gnews_client.py    # GNews ingestion (Week 1)
│   ├── hn_client.py       # Hacker News ingestion (Week 3)
│   ├── reddit_client.py   # Reddit ingestion via PRAW (Week 3)
│   └── _utils.py          # Shared datetime parsing utilities (Week 3)
├── processing/        # Data validation, transformation, & AI scoring logic
├── analytics/         # Reusable SQL analytics & aggregation layer
├── dashboard/         # Streamlit dashboard application
│   ├── components/    # Reusable UI components (Sidebar, Footer, Cards)
│   ├── pages/         # Dashboard pages
│   │   ├── 01_News_Explorer.py
│   │   ├── 02_Analytics.py
│   │   ├── 03_Top_AI_News.py
│   │   ├── 04_Insights.py
│   │   └── 05_Source_Analytics.py  ← Week 3
│   └── utils/         # Dashboard caching and UI formatting helpers
├── .streamlit/        # Streamlit configuration (theme, server settings)
├── scripts/           # Standalone verification & utility scripts
├── sql/               # Sample analytical queries (raw & staging)
├── tests/             # Unit tests for the data pipeline
│   ├── test_ingestion.py       # 11 GNews tests (Week 1/2)
│   ├── test_hn_client.py       # 5 HN tests (Week 3)
│   ├── test_reddit_client.py   # 6 Reddit tests (Week 3)
│   └── test_processing.py      # 8 processing layer tests (Week 3)
├── utils/             # Cross-cutting utilities (logging)
├── docs/              # Architecture diagrams & design documents
│
├── .env.example       # Template for environment variables
├── main.py            # Pipeline entry point — Ingests & Processes data
├── requirements.txt   # Pinned Python dependencies
└── README.md          # This file
```

---

## ⚙️ Quick Start

### Prerequisites

- Python 3.12+
- PostgreSQL 16
- Git

---

### Step 1: Install & Set Up PostgreSQL

1. Install PostgreSQL from [postgresql.org](https://www.postgresql.org/download/windows/).
2. Set a password for user `postgres`.
3. Open **pgAdmin** or `psql` and create the database:
   ```sql
   CREATE DATABASE ai_pulse_db;
   ```

---

### Step 2: Clone & Set Up Python

```bash
git clone https://github.com/YOUR_USERNAME/ai-pulse-warehouse.git
cd ai-pulse-warehouse

python -m venv venv
# Activate it (Windows PowerShell)
.\venv\Scripts\Activate.ps1
# Activate it (macOS/Linux)
source venv/bin/activate

pip install -r requirements.txt
```

---

### Step 3: Configure Environment Variables

```bash
copy .env.example .env        # Windows
cp .env.example .env          # macOS/Linux
```

Edit `.env` with your credentials:

| Variable | Required | Description |
|---|---|---|
| `GNEWS_API_KEY` | ✅ Yes | Free key from [gnews.io](https://gnews.io) |
| `DATABASE_URL` | ✅ Yes | PostgreSQL connection string |
| `REDDIT_CLIENT_ID` | ⬜ Optional | From [reddit.com/prefs/apps](https://www.reddit.com/prefs/apps) |
| `REDDIT_CLIENT_SECRET` | ⬜ Optional | Same as above |
| `REDDIT_USER_AGENT` | ⬜ Optional | Any descriptive string |

> **Note:** If Reddit credentials are absent, the pipeline skips Reddit and runs GNews + Hacker News only.

---

### Step 4: Run the Pipeline

Ingest from all sources and process into the staging table:
```bash
python main.py
```

Expected output:
```
==============================================================
   AI PULSE -- GenAI Industry Trends Warehouse
   Data Pipeline -- Week 1 + 2 + 3
   GNews + HackerNews + Reddit -> Validate -> Score -> PostgreSQL
==============================================================

[Source 1/3] GNews API...         → 10 articles
[Source 2/3] Hacker News...       → 10 articles
[Source 3/3] Reddit...            → 30 articles (or skipped)
Total articles merged: 20–50
```

---

### Step 5: Run Tests

```bash
pytest tests/ -v
```

Expected: **30 passed** in under 2 seconds.

---

### Step 6: Launch the Dashboard

```bash
streamlit run dashboard/app.py
```

Open [`http://localhost:8501`](http://localhost:8501) in your browser.

---

## 🗄️ Database Schema

The pipeline uses two primary tables following a Medallion-style architecture:

1. **`raw_ai_news`**: Append-only, untransformed JSON payload mapping. Every article from every source is stored here as ingested.
2. **`stg_ai_news`**: Cleaned, validated, normalized data enriched with an `intelligence_score` and `keywords_found`. The source field distinguishes GNews / Hacker News / Reddit articles.

No schema changes were needed for Week 3 — the existing `source` column on both tables accommodates all three ingestion sources automatically.

---

## 🗺️ Roadmap

| Status | Week | Theme | Key Additions |
|:---:|---|---|---|
| ✅ | **Week 1** | Foundation | GNews API → PostgreSQL `raw_ai_news` |
| ✅ | **Week 2** | Processing & UI | Validation, AI Scoring, `stg_ai_news`, Streamlit Dashboard |
| ✅ | **Week 3** | Multi-Source | HackerNews + Reddit ingestion, Source Analytics page, 30 tests |
| ⬜ | **Week 4** | Deploy | Dockerization, CI/CD, Live URL deployment |
| ⬜ | **Week 5** | Showcase | Portfolio presentation, Loom video, Resume bullets |

---

## 📝 Key Learnings (Week 1–3)

1. **Idempotency is critical:** `ON CONFLICT DO NOTHING` prevents duplicates when the same URL is found by two sources (e.g., GNews and HN both pick up a TechCrunch article).
2. **Source-agnostic design:** By standardising on 7 columns (`title, source, author, description, published_at, url, category`), any new data source can be added with zero changes to the processing or analytics layers.
3. **Medallion Architecture:** Keeping Raw data distinct from Staging/Clean data ensures we can always reprocess history without data loss.
4. **Optional credentials pattern:** Making Reddit ingestion conditional on credentials being present (not hard-failing) is the production-correct approach for optional enrichment sources.
5. **DRY at extraction level:** Moving shared utilities (`_parse_datetime`, `parse_unix_timestamp`) to `ingestion/_utils.py` instead of copying them into every client prevents logic divergence across ingestion modules.
6. **Mock the right target:** When a module imports a dependency at module level (`import praw`), tests must patch the reference in the importing module (`ingestion.reddit_client.praw`), not in the library itself.

---

## 📜 License

MIT License — free to use, modify, and distribute.

---

## 🙏 Acknowledgements

- **GNews API** — [gnews.io](https://gnews.io) — for providing free AI news data
- **Hacker News Firebase API** — [github.com/HackerNews/API](https://github.com/HackerNews/API) — free, unlimited, no auth
- **PRAW** — [praw.readthedocs.io](https://praw.readthedocs.io) — Python Reddit API Wrapper
- Built as part of the **Foundations of Data Engineering Internship** (June–July 2026)
