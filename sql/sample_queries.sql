-- =============================================================================
-- sql/sample_queries.sql — AI Pulse Project
-- =============================================================================
--
-- PURPOSE:
--   A collection of analytical SQL queries for exploring and understanding
--   the data stored in the raw_ai_news table.
--
-- HOW TO RUN:
--   Option 1 — pgAdmin (GUI):
--     Open pgAdmin → Query Tool → paste and execute each query
--
--   Option 2 — psql (command line):
--     psql -U postgres -d ai_pulse_db -f sql/sample_queries.sql
--
-- CONCEPT — Why Write SQL Queries Separately?
--   These queries are for ANALYSIS and EXPLORATION, not for the pipeline.
--   In Week 2, you'll write dbt models (SQL files with macros) that run
--   automatically as part of the pipeline. For now, we run these manually.
--
-- CONCEPT — Data Engineering SQL vs Application SQL:
--   Application SQL: SELECT user by ID, INSERT one order
--   DE SQL (Analytics): aggregate millions of rows, find patterns,
--                        answer business questions ("which source publishes most?")
--
-- =============================================================================


-- =============================================================================
-- QUERY 1: Total Articles in Warehouse
-- =============================================================================
-- Business Question: "How many articles have we collected so far?"
-- This is the most basic health check for a data warehouse.
-- Run this after every pipeline run to confirm data was loaded.
-- =============================================================================

SELECT
    COUNT(*)            AS total_articles,
    MIN(ingested_at)    AS first_ingested,      -- Earliest record in our warehouse
    MAX(ingested_at)    AS last_ingested,        -- Most recent ingestion run
    COUNT(DISTINCT source) AS unique_sources     -- How many different news sources
FROM
    raw_ai_news;


-- =============================================================================
-- QUERY 2: Latest 10 Articles (Most Recently Published)
-- =============================================================================
-- Business Question: "What are the most recent AI news articles we have?"
-- Analysts use this to verify data freshness and understand what's trending.
-- =============================================================================

SELECT
    title,
    source,
    author,
    published_at,
    LEFT(description, 100) AS description_preview,  -- First 100 chars of description
    url
FROM
    raw_ai_news
ORDER BY
    published_at DESC    -- Most recent first (DESC = descending = newest to oldest)
LIMIT 10;


-- =============================================================================
-- QUERY 3: Top News Sources by Article Count
-- =============================================================================
-- Business Question: "Which news sources cover AI the most?"
-- This helps analysts understand which sources to trust and track closely.
-- Useful for a future dashboard: "Top Publishers" bar chart.
-- =============================================================================

SELECT
    source,
    COUNT(*)                                    AS article_count,
    ROUND(
        COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 2
    )                                           AS percentage_of_total,
    MIN(published_at)                           AS earliest_article,
    MAX(published_at)                           AS latest_article
FROM
    raw_ai_news
WHERE
    source IS NOT NULL
    AND source != 'Unknown Source'
GROUP BY
    source
ORDER BY
    article_count DESC
LIMIT 20;

-- CONCEPT — Window Function (OVER()):
--   SUM(COUNT(*)) OVER() calculates the total count ACROSS ALL GROUPS,
--   allowing us to calculate each source's percentage of the total.
--   This is more efficient than running two separate queries.


-- =============================================================================
-- QUERY 4: Articles Per Day (Time Series)
-- =============================================================================
-- Business Question: "How does AI news volume change day by day?"
-- This is the foundation of a time-series chart in a BI dashboard.
-- Spikes in volume may indicate a major AI announcement (e.g., a new model release).
-- =============================================================================

SELECT
    DATE(published_at AT TIME ZONE 'UTC')   AS published_date,   -- Truncate to date only
    COUNT(*)                                AS articles_count,
    COUNT(DISTINCT source)                  AS unique_sources,
    STRING_AGG(DISTINCT source, ', ')       AS sources_list       -- Comma-separated list
FROM
    raw_ai_news
WHERE
    published_at IS NOT NULL
GROUP BY
    DATE(published_at AT TIME ZONE 'UTC')
ORDER BY
    published_date DESC;

-- CONCEPT — DATE():
--   published_at is TIMESTAMP WITH TIMEZONE.
--   DATE() strips the time part, leaving just the date (2026-06-24).
--   This lets us GROUP BY day instead of by exact timestamp.


-- =============================================================================
-- QUERY 5: Search Articles by Keyword
-- =============================================================================
-- Business Question: "How many articles mention OpenAI specifically?"
-- Useful for tracking coverage of specific companies.
-- In Week 2, this becomes a parameterized dbt model.
-- =============================================================================

SELECT
    title,
    source,
    published_at,
    url
FROM
    raw_ai_news
WHERE
    LOWER(title) LIKE '%openai%'          -- Case-insensitive search in title
    OR LOWER(description) LIKE '%openai%'  -- Also search in description
ORDER BY
    published_at DESC;

-- Change 'openai' to 'google gemini', 'anthropic', 'nvidia', etc.
-- to track any company or keyword.


-- =============================================================================
-- QUERY 6: Data Quality Check
-- =============================================================================
-- Business Question: "Are there any data quality issues in our raw table?"
-- A Senior DE always checks data quality before trusting the data.
-- This query helps identify missing or empty values.
-- =============================================================================

SELECT
    COUNT(*)                                                    AS total_rows,
    SUM(CASE WHEN title IS NULL OR title = '' THEN 1 ELSE 0 END)       AS missing_title,
    SUM(CASE WHEN source IS NULL OR source = '' THEN 1 ELSE 0 END)     AS missing_source,
    SUM(CASE WHEN author IS NULL OR author = 'Unknown' THEN 1 ELSE 0 END) AS unknown_author,
    SUM(CASE WHEN description IS NULL THEN 1 ELSE 0 END)               AS missing_description,
    SUM(CASE WHEN published_at IS NULL THEN 1 ELSE 0 END)              AS missing_date,
    SUM(CASE WHEN url IS NULL OR url = '' THEN 1 ELSE 0 END)           AS missing_url
FROM
    raw_ai_news;

-- CONCEPT — Data Quality in DE:
--   In production, you would run these checks automatically after every ingestion.
--   Tools like Great Expectations (Week 3+) automate this process.
--   For now, run this manually to understand your data.


-- =============================================================================
-- QUERY 7: Ingestion Run History
-- =============================================================================
-- Business Question: "When did we run the pipeline, and how many records each time?"
-- This shows you a timeline of all your pipeline runs.
-- =============================================================================

SELECT
    DATE_TRUNC('minute', ingested_at)   AS ingestion_run_time,
    COUNT(*)                            AS records_loaded,
    COUNT(DISTINCT source)              AS sources_covered
FROM
    raw_ai_news
GROUP BY
    DATE_TRUNC('minute', ingested_at)
ORDER BY
    ingestion_run_time DESC;

-- CONCEPT — DATE_TRUNC():
--   Rounds a timestamp to the specified precision.
--   'minute' → groups all records loaded within the same minute together,
--   which approximates one pipeline run (since main.py runs in < 60 seconds).
