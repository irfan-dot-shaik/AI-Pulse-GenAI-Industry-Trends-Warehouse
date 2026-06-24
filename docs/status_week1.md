# Week 1 Status One-Pager — AI Pulse

**Date:** June 24, 2026
**Demo:** Friday Demo #1
**Week Theme:** Foundation + Architecture
**Student:** B.Tech CSE-AIDE, 2nd Year
**Project:** H1 — APIs to Warehouse (Foundations of Data Engineering)

---

## Project Summary

**AI Pulse** is a data pipeline that automatically ingests AI-related news from the GNews public API, stores it in a PostgreSQL data warehouse, and prepares clean datasets for analysis. The end goal is a fully deployed, multi-source analytics system by Week 5.

---

## Week 1 Completion Status

| Deliverable | Status | Notes |
|---|---|---|
| Public GitHub Repository | ✅ Complete | Clean structure, 7 commits |
| Professional Folder Structure | ✅ Complete | 7 modules, modular design |
| Initial README | ✅ Complete | All mandatory sections included |
| Design Document | ✅ Complete | `docs/design_doc.md` |
| Architecture Diagram | ✅ Complete | `docs/architecture.md` |
| Config Module | ✅ Complete | `.env` based, validated |
| Ingestion Layer (GNews) | ✅ Complete | Error handling, returns DataFrame |
| Database Layer (PostgreSQL) | ✅ Complete | ORM models, idempotent upsert |
| Logging Utility | ✅ Complete | Console + file, structured format |
| Unit Tests | ✅ Complete | 10 tests, mocking, no API needed |
| Pipeline Orchestrator | ✅ Complete | `main.py` — 5-step flow |
| Sample SQL Queries | ✅ Complete | 7 analytical queries |
| requirements.txt | ✅ Complete | All versions pinned |
| .env.example | ✅ Complete | Template for secrets |
| .gitignore | ✅ Complete | Secrets protected |

---

## Architecture (Week 1)

```
GNews API → Python Ingestion → Pandas DataFrame → PostgreSQL (raw_ai_news)
```

**Key Engineering Decisions:**
1. **Idempotency via URL UNIQUE constraint** — running twice doesn't duplicate records
2. **Fail Fast config validation** — bad `.env` caught at startup, not midway
3. **Modular architecture** — each module has one responsibility
4. **Centralized logging** — every action is timestamped and saved to file
5. **ORM over raw SQL** — safer, more readable, database-agnostic

---

## What I Can Explain

By the end of Week 1, I can explain:

- ✅ What an API is and how HTTP requests work
- ✅ Why we use environment variables for secrets (not hardcoding)
- ✅ What a Pandas DataFrame is and why we use it
- ✅ What SQLAlchemy ORM is and why it's better than raw SQL
- ✅ What idempotency means and how URL UNIQUE enforces it
- ✅ What `ON CONFLICT DO NOTHING` does in PostgreSQL
- ✅ The difference between `published_at` and `ingested_at`
- ✅ Why we use `logging` instead of `print()`
- ✅ What a unit test is and how mocking works
- ✅ The Data Engineering naming convention: `raw_` → `stg_` → `fct_`

---

## Challenges Faced

| Challenge | Resolution |
|---|---|
| GNews free tier returns max 10 articles | Accepted for Week 1; will add multiple API calls in Week 2 |
| Author field not provided by GNews | Defaults to "Unknown"; Reddit API (Week 3) will provide real authors |
| Datetime timezone handling | Used `datetime.fromisoformat()` with UTC enforcement |

---

## Next Week (Week 2) Plan

- [ ] Build `dbt` project for SQL transformations (`stg_ai_news`, `fct_ai_articles`)
- [ ] Write Architecture Decision Records (ADRs) for API, DB, and stack choices
- [ ] Add retry mechanism for failed API calls (exponential backoff)
- [ ] Increase article volume using GNews `from/to` date parameters
- [ ] Build "skinny" end-to-end: raw → staging → mart → query result

---

## Git Commit History

```
1. chore: initialize project structure and .gitignore
2. feat: add config module with settings and env loading
3. feat: implement GNews API ingestion client
4. feat: add SQLAlchemy models and warehouse loader
5. feat: add centralized logging utility
6. feat: wire main pipeline orchestrator
7. docs: add README, design doc, and sample SQL queries
```

---

*Prepared for Friday Demo #1 | Week 1 — Foundation + Architecture*
