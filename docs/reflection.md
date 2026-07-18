# Internship Reflection — AI Pulse: GenAI Industry Trends Warehouse

**Author:** Irfan Shaik  
**Project:** AI Pulse – GenAI Industry Trends Warehouse  
**Stack:** Python · PostgreSQL · SQLAlchemy · Streamlit · Plotly · Docker · GNews API · Hacker News API  
**Period:** June – July 2026

---

## 1. What I Built

### Overview

AI Pulse is a production-grade data engineering project that solves a real business problem: keeping analysts informed about trends in the Generative AI industry without spending hours manually browsing news websites. The system automatically ingests AI-related news articles from multiple public APIs, validates and transforms them through a multi-stage ETL pipeline, stores them in a PostgreSQL data warehouse, computes an AI Intelligence Score for each article, and surfaces everything through an interactive, Bloomberg-style analytics dashboard.

### The Problem Being Solved

Before this project, an analyst tracking the GenAI space would spend three to five hours per day visiting individual websites, reading unfiltered content, and manually deciding what was worth reading. That process was inconsistent across team members, impossible to trend over time, and always behind the news cycle. AI Pulse replaces that manual workflow with a structured, reproducible pipeline that runs daily and delivers ranked, scored intelligence to a single dashboard.

### Architecture

The system follows a medallion-inspired architecture with three layers: Raw, Staging, and Analytics.

- **Raw layer** (`raw_ai_news`): Stores unprocessed articles exactly as received from each API, preserving a full audit trail.
- **Staging layer** (`stg_ai_news`): Cleaned, deduplicated, and validated articles with all transformations applied.
- **Analytics layer**: SQL views and aggregations built on top of the staging table, consumed by the dashboard.

The ingestion pipeline pulls from two sources — GNews API and the Hacker News REST API — normalises the schemas into a common format, and loads them into PostgreSQL via SQLAlchemy. A validation step runs on each record before it is promoted to the staging table. Every article then receives an intelligence score between 0 and 100, computed from a weighted formula that considers keyword density, source credibility, recency, and content length.

### Dashboard Capabilities

The Streamlit frontend has seven pages:

1. **Overview** — Live KPI cards (total articles, today's count, source count, average score), recent top articles, pipeline health indicators.
2. **News Explorer** — Full search and filter interface with keyword search, source filter, score category filter, sort options, score range slider, and paginated article cards. Includes a working reset button.
3. **Analytics** — Six KPI cards, five Plotly charts (source distribution, trend line, category donut, keyword frequency, score histogram), publisher performance table, and a top-10 articles list.
4. **Top AI News** — Top-scored articles with quick filter controls, trending company mentions, and a keyword cloud.
5. **Source Analytics** — Per-source breakdown with quality metrics, keyword comparison, and daily trend lines split by source.
6. **Insights & Intelligence** — Auto-generated narrative insights, pipeline monitoring KPIs, data quality metrics, and data-driven recommendations.
7. **About** — Project documentation covering architecture, tech stack, phase journey, and future scope.

---

## 2. What I Learned About the Tools

### PostgreSQL

Before this project, my experience with databases was limited to simple SELECT queries in academic exercises. During this project I learned to design proper database schemas, unique constraints, indexing strategies, analytical SQL queries, and query optimization techniques. I also gained a deeper understanding of data warehouse design principles and why raw and staging layers should remain logically separated.

### SQLAlchemy

I learned to use SQLAlchemy both as a connection manager and as a query layer without needing raw psycopg2. The `create_engine()` pattern with connection pooling made the Streamlit dashboard significantly more stable under concurrent loads. I also learned the importance of using `@st.cache_resource` to share the engine across reruns rather than opening a new connection on every user interaction.

### Streamlit

Streamlit's simplicity is deceptive. Building a dashboard that looks and behaves like a production application required deep understanding of how Streamlit re-executes the entire script on every interaction. Managing `st.session_state` correctly was the most technically challenging part of this project — particularly around the filter reset buttons, which triggered a `StreamlitAPIException` when I tried to modify widget keys after they were instantiated. Solving that required implementing the reset flag pattern: setting a flag in session state and performing the reset at the top of the next execution cycle, before widgets are rendered. That was a real debugging breakthrough that taught me how Streamlit's execution model actually works.

### Docker

Containerising the project forced me to think about the full system holistically — environment variables, service dependencies, port mapping, and startup order. Writing a `docker-compose.yml` that correctly sequences the PostgreSQL service before the Streamlit app, and wiring environment variables through `.env` files, gave me practical experience with the kind of infrastructure decisions that matter in a real deployment.

### API Integration

Working with multiple APIs taught me that no two data sources return data in the same shape. GNews returns structured JSON with consistent timestamps. Hacker News requires recursive requests to fetch both story metadata and nested comments. Building a normalisation layer that maps both formats into the same internal schema — with proper null handling, type coercion, and deduplication by URL — was far more complex than I anticipated and is genuinely one of the most important skills in data engineering.

### ETL Pipelines and Multi-Source Ingestion

This project gave me firsthand experience with the classic ETL challenges: API rate limits, missing fields, duplicate articles published across sources, timezone inconsistencies, and data quality degradation over time. Building an automated daily pipeline that handles these edge cases reliably taught me that robustness matters far more than feature richness in production data systems.

---

## 3. What I Learned About Myself

### Problem Solving Under Pressure

The hardest moments of this project were not technical — they were psychological. When the entire dashboard went down due to a Python `IndentationError` at line 652 of `styles.py`, or when the reset button started crashing with a `StreamlitAPIException` on every click, the temptation was to panic and start rewriting large sections of code. I learned to slow down, read error tracebacks carefully, isolate the smallest possible reproduction case, and fix only what was broken. That discipline improved my debugging speed dramatically over the course of the project.

### The Gap Between "Working" and "Production-Ready"

I learned that getting something to work is perhaps 40% of the effort. The other 60% is making it reliable, readable, and presentable. Production polish — consistent typography, pixel-aligned filter layouts, professional empty states, graceful error boundaries, and zero dead code — takes longer than the initial feature. This was frustrating at first, but I now understand why it matters: a tool that looks unfinished will not be trusted, regardless of how solid the underlying data is.

### Consistency and Commitment

There were days when progress was invisible. The pipeline worked, the data loaded correctly, but the dashboard still looked rough. I learned to trust incremental progress and maintain the habit of daily improvement rather than waiting for inspiration. Consistency turned out to be a more reliable driver of quality than any single breakthrough moment.

### Scope Management

I over-engineered several parts of this project early on and then had to refactor them. The initial session_state management was one example. I had added complex caching and cleanup logic that introduced more bugs than it prevented. Simplifying it down to a straightforward flag pattern resolved everything. This reinforced the principle of building the simplest thing that works correctly, then extending it once the foundation is stable.

---

## 4. What I'd Do Differently

### Plan the Schema Before Writing Any Pipeline Code

I refactored the database schema twice during this project. If I had spent one full day upfront designing the raw, staging, and analytics layers with their column types, constraints, and indexes, I would have saved at least three days of downstream rework. Schema design deserves the same rigour as application design.

### Write Tests Before Building Features

I added unit tests towards the end of the project when many of the edge cases were already fixed. Writing tests first would have caught issues like the score calculation edge cases and the null-handling bugs in the formatters much earlier, and would have given me confidence to refactor without fear of breaking something.

### CI/CD From Day One

Setting up a basic GitHub Actions workflow to run the test suite on every push is a ten-minute task. I delayed it until the project was nearly complete. Having it from the start would have prevented several instances of committing broken code that only showed up when running the full pipeline.

### Centralise Configuration Earlier

I had hardcoded strings scattered across multiple files before consolidating them into a single configuration module. This made early refactors painful. A single `config.py` or `.env`-driven constants file from the start would have made the codebase significantly more maintainable.

---

## 5. What's Next

The most immediate priority is adding **workflow orchestration** — replacing the manual `python main.py` invocation with Apache Airflow or Prefect so the pipeline runs automatically on a daily schedule. This is table-stakes for any production data pipeline.

After that, I want to explore **real-time ingestion** using Kafka or a similar message queue, so that breaking AI news surfaces in the dashboard within minutes rather than hours. This would require moving from batch scoring to streaming scoring, which is a significant architectural change worth learning.

On the intelligence side, I want to experiment with **LLM-powered summarisation** — using a small open-source language model to generate a one-sentence summary of each article automatically, which would make the Top AI News feed genuinely more useful than raw headlines.

Longer term, I want to add **user authentication and personalised alerts** so that users can subscribe to specific companies, keywords, or score thresholds and receive email or Slack notifications when relevant articles are ingested.

The bigger career goal that this project has clarified: I want to become a data or ML engineer who can own the full pipeline from ingestion to insight, not just one layer of it. AI Pulse showed me that this kind of end-to-end ownership is both achievable and deeply satisfying.

---

*This reflection was written at the conclusion of a five-week internship project. The system is deployed locally via Docker and the full source code is version-controlled on GitHub.*
