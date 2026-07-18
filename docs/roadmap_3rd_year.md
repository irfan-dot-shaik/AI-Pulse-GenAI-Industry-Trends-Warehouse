# AI Pulse — 3rd Year Development Roadmap

**Project:** AI Pulse – GenAI Industry Trends Warehouse  
**Author:** Irfan Shaik  
**Vision:** Transform AI Pulse from a final-year internship showcase into an enterprise-grade AI Industry Intelligence Platform  
**Timeframe:** August 2026 – December 2026

---

## Current State (Internship Baseline)

At the conclusion of the internship, AI Pulse is a fully functional, production-ready data warehouse and analytics dashboard with the following capabilities:

| Capability | Status |
|---|---|
| Multi-source ingestion (GNews + Hacker News) | ✅ Production |
| ETL pipeline with validation and transformation | ✅ Production |
| AI Intelligence Scoring (0–100) | ✅ Production |
| PostgreSQL data warehouse (raw + staging layers) | ✅ Production |
| 7-page Streamlit analytics dashboard | ✅ Production |
| Docker deployment | ✅ Production |
| Unit test suite (30+ tests) | ✅ Production |
| Architecture documentation | ✅ Production |

**Limitations of the current system:**

- Pipeline is triggered manually (`python main.py`) — no scheduler
- No automated monitoring or alerting
- No CI/CD pipeline
- Batch-only ingestion — no real-time capability
- No user authentication or multi-user support
- No LLM-powered summarisation or trend prediction
- Limited to two data sources (GNews and Hacker News)

---

## August – September 2026: Foundations & Expansion

**Theme: Stabilise, Automate, Expand**

The goal for the first two months is to close the gaps in the current system — adding orchestration, more data sources, and a proper CI/CD pipeline — without adding major new features that would destabilise the codebase.

### Data Sources

- [ ] **Add Reddit API (PRAW)** — Developer community sentiment and discussion threads
- [ ] **Add ArXiv API** — Academic papers on LLMs and GenAI, providing research-level signal
- [ ] **Add Dev.to RSS feed** — Developer blog posts and tutorials for broader coverage

### Pipeline Orchestration

- [ ] **Migrate from manual scripts to Apache Airflow**
  - Define a `daily_ingest_dag` that runs at 06:00 UTC
  - Separate tasks for each source (GNews, Hacker News, Reddit, ArXiv)
  - Add email alerts on pipeline failure
  - Retry logic with exponential backoff on API failures

- [ ] **Alternative: Prefect (lighter option for solo development)**
  - Prefect Cloud free tier supports scheduled flows
  - Simpler setup than a full Airflow deployment
  - Good choice if running on a single machine or small VM

### Intelligence Scoring Improvements

- [ ] **Source credibility weighting** — Weight GNews articles from major publishers (Reuters, BBC, TechCrunch) higher than unknown blogs
- [ ] **Engagement signal** — Incorporate Hacker News comment count and Reddit upvote ratio into the score formula
- [ ] **Recency decay** — Apply exponential time decay so articles from 7+ days ago score lower regardless of keyword density

### Dashboard Additions

- [ ] **Score history chart** — Show how average intelligence score has changed over the past 90 days
- [ ] **Source quality leaderboard** — Rank sources by average article score over time
- [ ] **Keyword trend sparklines** — Mini-charts showing whether a keyword is rising or falling week-on-week

---

## October – November 2026: Engineering Maturity

**Theme: Reliability, Observability, Quality**

By October, the pipeline should be running automatically and reliably. This phase focuses on building the engineering infrastructure that makes a project trustworthy rather than just functional.

### CI/CD Pipeline

- [ ] **GitHub Actions workflow**
  - Run the full test suite (`pytest`) on every pull request to `main`
  - Run `flake8` lint check on every push
  - Block merges if any test fails
  - Add a badge to the README showing test status

- [ ] **Environment separation**
  - Create separate `dev`, `staging`, and `prod` environment configs
  - Use `.env.dev`, `.env.prod` files managed through GitHub Secrets for deployment

### Testing Improvements

- [ ] **Integration tests** — Test the full ETL pipeline against a test PostgreSQL database
- [ ] **Data contract tests** — Verify that each source adapter always returns the required fields (`title`, `url`, `published_at`, `source`)
- [ ] **Regression tests** — Lock the intelligence scoring formula with expected output tests so formula changes are intentional

### Data Quality Framework

- [ ] **Great Expectations integration**
  - Define expectations: `title` must not be null, `url` must be unique, `intelligence_score` must be between 0 and 100
  - Run expectations as part of the daily pipeline
  - Generate a data quality HTML report after each run

### Monitoring

- [ ] **Pipeline health dashboard** (extend existing Insights page)
  - Track daily article count per source over 30 days
  - Alert if any source returns 0 articles (likely API failure)
  - Track pipeline run duration and flag runs that take unusually long

- [ ] **Logging improvements**
  - Structured JSON logs for every pipeline run
  - Log to a file with daily rotation
  - Capture ingestion count, validation failure rate, and scoring duration per run

---

## November – December 2026: Real-Time & Intelligence

**Theme: Stream Processing, LLM Features, Observability**

The final phase of the year introduces the most ambitious features: real-time data ingestion, language model integration, and production-grade observability. These are the features that move AI Pulse from a data warehouse into an intelligence platform.

### Streaming Architecture

- [ ] **Apache Kafka integration**
  - Publish each new article to a Kafka topic immediately after ingestion
  - Separate consumer groups for scoring, deduplication, and dashboard updates
  - This removes the 24-hour batch cycle — articles appear in the dashboard within seconds

- [ ] **Real-time dashboard updates**
  - Use Streamlit's `st.rerun` with a background thread or WebSocket connection to refresh the Overview page automatically when new articles arrive
  - Live article counter that increments without a page reload

### LLM-Powered Features

- [ ] **Automated article summarisation**
  - Use Ollama with Mistral 7B (runs locally, free) to generate a 2-sentence summary for each article
  - Store summaries in the staging table
  - Display summaries in article cards on the Explorer and Top AI News pages

- [ ] **Trend narrative generation**
  - Once per day, pass the top 20 articles to an LLM with a prompt asking for a 3-paragraph narrative of what's trending in GenAI today
  - Display this as the "Market Intelligence Brief" on the Overview page

- [ ] **Sentiment classification**
  - Fine-tune or prompt a small model to classify each article as Positive / Neutral / Negative about a given topic (e.g., "Is this article optimistic about AGI?")
  - Add a sentiment filter to the News Explorer

### Observability

- [ ] **Grafana + Prometheus stack**
  - Instrument the pipeline to emit metrics (articles ingested, API errors, scoring latency) to Prometheus
  - Build a Grafana dashboard showing pipeline health over time
  - Set up alerts for error rate exceeding a threshold

- [ ] **Sentry error tracking**
  - Integrate Sentry SDK to capture unhandled exceptions in both the pipeline and the dashboard
  - Real-time error notifications to email or Slack

### Alerts and Notifications

- [ ] **Keyword alert system**
  - Users can subscribe to keywords (e.g., "GPT-5", "OpenAI regulation")
  - When an article matching a subscribed keyword scores above 75, send an email notification
  - Requires adding a simple user model and SMTP integration

---

## 3rd Year Internship Vision

### Target State by End of 3rd Year

> **Enterprise AI Industry Intelligence Platform**

A system that any analyst, researcher, or product manager at an AI company would genuinely want to use every day. Not a student project with a polished UI, but a system that provides real, actionable intelligence automatically.

### Feature Vision

| Feature | Priority | Difficulty |
|---|---|---|
| Real-time Kafka ingestion | High | Hard |
| LLM article summarisation | High | Medium |
| Scheduled Airflow orchestration | High | Medium |
| Great Expectations data quality | High | Medium |
| GitHub Actions CI/CD | High | Easy |
| Grafana + Prometheus observability | Medium | Hard |
| Sentiment classification | Medium | Medium |
| Keyword alert notifications | Medium | Medium |
| User authentication (OAuth) | Medium | Hard |
| Trend prediction (ML model) | Low | Very Hard |
| Full-text search (Elasticsearch) | Low | Hard |
| Multi-tenant SaaS mode | Low | Very Hard |

### Skills to Develop

| Skill | Where Practised |
|---|---|
| Workflow orchestration | Airflow / Prefect |
| Stream processing | Kafka |
| Data quality | Great Expectations |
| Observability | Grafana + Prometheus |
| LLM integration | Ollama / OpenAI API |
| CI/CD | GitHub Actions |
| Cloud deployment | AWS EC2 / Railway / Render |
| Infrastructure as code | Docker Compose → Terraform |

### Milestone Targets

| Date | Target |
|---|---|
| Sep 2026 | Airflow DAG running daily · Reddit + ArXiv sources live |
| Oct 2026 | GitHub Actions CI/CD · Great Expectations integrated |
| Nov 2026 | Kafka streaming · LLM summarisation prototype |
| Dec 2026 | Grafana monitoring · Keyword alerts · 3rd year demo-ready |

---

## Guiding Principles

1. **Build for reliability first.** A pipeline that runs every day without breaking is more valuable than one with impressive features that occasionally fails.

2. **Measure everything.** If you cannot observe what the system is doing, you cannot improve it. Add metrics and logging before adding features.

3. **Test before merging.** The CI/CD pipeline is not optional — it is the safety net that makes moving fast sustainable.

4. **Learn in production.** Deploy early, deploy often. Running on a live server with real data reveals problems that no amount of local testing will find.

5. **Document decisions, not just features.** Future-you will not remember why a particular architecture choice was made. Write it down at the time.

---

*This roadmap is a living document. It should be reviewed and updated at the start of each semester based on what was achieved, what was learned, and what has changed in the technology landscape.*
