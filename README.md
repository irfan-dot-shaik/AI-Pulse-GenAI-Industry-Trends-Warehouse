# AI Pulse — GenAI Industry Trends Warehouse

> **Automatically ingests AI news from public APIs, stores it in a PostgreSQL warehouse, validates and transforms it, and serves it through a production-ready Streamlit analytics dashboard.**

![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791?logo=postgresql)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0-red)
![Pandas](https://img.shields.io/badge/Pandas-2.1-150458?logo=pandas)
![Streamlit](https://img.shields.io/badge/Streamlit-1.35+-FF4B4B?logo=streamlit)
![Plotly](https://img.shields.io/badge/Plotly-5.22-3f4f75?logo=plotly)
![License](https://img.shields.io/badge/License-MIT-green)
![Week](https://img.shields.io/badge/Week-2%20of%205-orange)

---

## 📌 Project Overview

**AI Pulse** is a Data Engineering portfolio project built during a 5-week internship (June–July 2026). It simulates real Junior Data Engineer work at a fictional startup that sells insights about the Generative AI industry.

The project evolves week-by-week from a simple API → PostgreSQL pipeline into a fully deployed, multi-source analytics system with dashboards, containerization, and production-grade practices.

**This repository represents Week 2** — The Processing & Analytics UI layer. We have built upon Week 1's raw ingestion by adding data validation, data transformation, AI intelligence scoring, a robust SQL analytics layer, and a professional, interactive Streamlit dashboard.

---

## 🚨 Business Problem

Analysts and researchers at AI Pulse currently spend **3–5 hours per day** manually browsing news websites to understand trends in the Generative AI space. This process is:

- **Inconsistent** — different analysts use different sources
- **Non-reproducible** — no historical data is saved for trend analysis
- **Slow** — analysis is always behind real-time events

**Solution:** Build a reusable data pipeline that automatically collects AI news every day, stores it in a structured warehouse, assigns an *AI Intelligence Score* to filter out noise, and presents actionable insights through a premium financial-style Executive Dashboard.

---

## ✨ Features (New in Week 2)

- **AI News Ingestion Pipeline:** Automated ingestion of JSON news data into a structured Raw layer.
- **PostgreSQL Data Warehouse:** Robust database schema managing both `raw_ai_news` and `stg_ai_news`.
- **Data Validation & Transformation:** Pandas-based pipeline steps to clean titles, normalize publisher names, and filter out low-quality articles.
- **AI Intelligence Scoring:** Custom heuristic algorithm assigning a 0-100 score to articles based on keyword density, source reputation, and content depth.
- **SQL Analytics Layer:** Reusable analytical queries wrapping complex aggregations.
- **Interactive Streamlit Dashboard:** A multi-page, polished, premium UI consisting of:
  - **Overview:** Project context and system status.
  - **News Explorer:** Advanced search, filtering, and pagination over the warehouse.
  - **Analytics:** Visualizing trends, source distributions, and intelligence score distributions via Plotly.
  - **Top AI News:** Curated feed of the highest-scoring, most impactful articles.
  - **Insights:** High-level executive KPIs derived dynamically from the analytics layer.

---

## 🏗️ Architecture

```text
┌─────────────────────────────────────────────────────────────────────────┐
│                     AI PULSE — WEEK 2 ARCHITECTURE                      │
└─────────────────────────────────────────────────────────────────────────┘

  ┌──────────────┐     HTTP GET      ┌─────────────────────┐
  │  GNews API   │ ─────────────────▶│  ingestion/         │
  └──────────────┘   JSON Response   │  gnews_client.py    │
                                     └──────────┬──────────┘
                                                │
                                     ┌──────────▼──────────┐
                                     │  database/          │
                                     │  raw_ai_news        │ (Raw Layer)
                                     └──────────┬──────────┘
                                                │
                                     ┌──────────▼──────────┐
                                     │  processing/        │
                                     │  validator.py       │
                                     │  transformer.py     │
                                     │  scorer.py          │
                                     └──────────┬──────────┘
                                                │
                                     ┌──────────▼──────────┐
                                     │  database/          │
                                     │  stg_ai_news        │ (Staging Layer)
                                     └──────────┬──────────┘
                                                │
                                     ┌──────────▼──────────┐
                                     │  analytics/         │
                                     │  queries.py         │ (SQL Aggregations)
                                     └──────────┬──────────┘
                                                │
                                     ┌──────────▼──────────┐
                                     │  dashboard/         │ (Streamlit App)
                                     │  app.py + pages/    │
                                     └─────────────────────┘
```

**Full architecture details:** → [`docs/architecture.md`](docs/architecture.md)

---

## 🛠️ Tech Stack

| Tool | Version | Purpose |
|---|---|---|
| **Python** | 3.11 | Core language for ingestion and transformation |
| **requests** | 2.31.0 | HTTP library for calling the GNews API |
| **pandas** | 2.1.4 | Transform JSON responses into DataFrames and clean data |
| **SQLAlchemy** | 2.0.25 | ORM — define tables as Python classes |
| **psycopg2-binary** | 2.9.9 | PostgreSQL connector (used by SQLAlchemy) |
| **PostgreSQL** | 16 | Data warehouse (raw and staging storage layer) |
| **Streamlit** | 1.35+ | Interactive web dashboard framework |
| **Plotly** | 5.22.0 | Advanced interactive data visualization |
| **pytest** | 7.4.4 | Unit testing framework |
| **python-dotenv** | 1.0.0 | Load `.env` secrets into environment variables |

---

## 📁 Project Structure

```text
ai-pulse-warehouse/
│
├── config/            # Centralized settings & environment variables
├── database/          # SQLAlchemy models & warehouse engine logic
├── ingestion/         # API clients (GNews)
├── processing/        # Data validation, transformation, & AI scoring logic
├── analytics/         # Reusable SQL analytics & aggregation layer
├── dashboard/         # Streamlit dashboard application
│   ├── components/    # Reusable UI components (Sidebar, Footer, Cards)
│   ├── pages/         # Dashboard pages (Explorer, Analytics, Top News, Insights)
│   └── utils/         # Dashboard caching and UI formatting helpers
├── .streamlit/        # Streamlit configuration (theme, server settings)
├── scripts/           # Standalone verification & utility scripts
├── sql/               # Sample analytical queries (raw & staging)
├── tests/             # Unit tests for the data pipeline
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

- Python 3.11+
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
Edit `.env` to include your GNews API key and Database URL.

---

### Step 4: Run the Pipeline

Ingest raw data and process it into the staging table:
```bash
python main.py
```

---

### Step 5: Launch the Dashboard

```bash
streamlit run dashboard/app.py
```
*The Streamlit dashboard will automatically open in your browser at `http://localhost:8501`, providing a polished, interactive interface to explore your warehouse data.*

---

## 🗄️ Database Schema

The pipeline now utilizes two primary tables representing a Medallion-style architecture:

1. **`raw_ai_news`**: Append-only, untransformed JSON payload mapping.
2. **`stg_ai_news`**: Cleaned, validated, normalized data enriched with an `intelligence_score`.

---

## 🗺️ Roadmap

| Status | Week | Theme | Key Additions |
|:---:|---|---|---|
| ✅ | **Week 1** | Foundation | GNews API → PostgreSQL `raw_ai_news` |
| ✅ | **Week 2** | Processing & UI | Validation, AI Scoring, `stg_ai_news`, Streamlit Dashboard |
| ⬜ | **Week 3** | Extension | Reddit/HackerNews ingestion, Data Quality Tests |
| ⬜ | **Week 4** | Deploy | Dockerization, CI/CD, Live URL deployment |
| ⬜ | **Week 5** | Showcase | Portfolio presentation, Loom video, Resume bullets |

---

## 📝 Key Learnings (Week 1 & 2)

1. **Idempotency is critical:** `ON CONFLICT DO NOTHING` prevents duplicates during automated ingestion.
2. **Separation of Concerns:** Splitting code into `ingestion/`, `processing/`, `database/`, and `analytics/` creates a scalable, testable architecture.
3. **Medallion Architecture:** Keeping Raw data distinct from Staging/Clean data ensures we can always reprocess history without data loss.
4. **Data Validation:** Assuming APIs return perfect data is dangerous; Pandas `.dropna()` and type enforcement prevent downstream warehouse corruption.
5. **UI/UX in Data Engineering:** A highly polished, robust frontend (Streamlit) bridges the gap between raw backend databases and business stakeholders.

---

## 📜 License

MIT License — free to use, modify, and distribute.

---

## 🙏 Acknowledgements

- **GNews API** — gnews.io — for providing free AI news data
- Built as part of the **Foundations of Data Engineering Internship** (June–July 2026)
