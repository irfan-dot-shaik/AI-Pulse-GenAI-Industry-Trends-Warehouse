-- =============================================================================
-- sql/analytics_queries.sql — AI Pulse Project
-- =============================================================================
--
-- PURPOSE:
--   SQL reference for all analytics queries used by the dashboard.
--   These are the same queries implemented as Python functions in
--   analytics/queries.py. This file exists for:
--     1. Portfolio / documentation purposes
--     2. Testing queries directly in psql or pgAdmin
--     3. Mentor review of SQL skills
--
-- TARGET TABLE: stg_ai_news (staging layer)
--   All analytics run against the STAGING table, not raw.
--   The raw table is the audit trail — analytics never touch it directly.
--
-- HOW TO RUN:
--   psql -U postgres -d ai_pulse_db -f sql/analytics_queries.sql
--
-- =============================================================================


-- =============================================================================
-- SECTION 1: KPI Queries (Dashboard Header Cards)
-- =============================================================================

-- 1.1 Total Articles in Staging
-- Used for: Dashboard "Total Articles" KPI card
SELECT COUNT(*) AS total_articles
FROM stg_ai_news;


-- 1.2 Articles Published Today
-- Used for: Dashboard "Today's Articles" KPI card
SELECT COUNT(*) AS todays_articles
FROM stg_ai_news
WHERE DATE(published_at AT TIME ZONE 'UTC') = CURRENT_DATE;


-- 1.3 Unique News Sources
-- Used for: Dashboard "Unique Sources" KPI card
SELECT COUNT(DISTINCT source) AS unique_sources
FROM stg_ai_news;


-- 1.4 Last Pipeline Run Time
-- Used for: Dashboard "Last Updated" KPI card
SELECT MAX(processed_at) AS last_run
FROM stg_ai_news;


-- 1.5 Average Intelligence Score
-- Used for: Analytics page quality metric
SELECT ROUND(AVG(intelligence_score), 1) AS avg_intelligence_score
FROM stg_ai_news;


-- =============================================================================
-- SECTION 2: Chart Data Queries (Analytics Page)
-- =============================================================================

-- 2.1 Articles Per Source (Top 10)
-- Used for: "Top Sources" bar chart
-- Shows which publishers are contributing the most AI news
SELECT
    source,
    COUNT(*) AS article_count
FROM stg_ai_news
WHERE source IS NOT NULL AND source != ''
GROUP BY source
ORDER BY article_count DESC
LIMIT 10;


-- 2.2 Articles Per Day (Last 30 Days)
-- Used for: "Articles Over Time" line chart
-- Shows publication volume trends over the past month
SELECT
    DATE(published_at AT TIME ZONE 'UTC') AS publish_date,
    COUNT(*)                               AS article_count
FROM stg_ai_news
WHERE published_at >= NOW() - INTERVAL '30 days'
  AND published_at IS NOT NULL
GROUP BY publish_date
ORDER BY publish_date ASC;


-- 2.3 Daily Ingestion Trend (Last 7 Days)
-- Used for: Pipeline activity trend chart
-- Shows how much data our pipeline ingested per day (vs. published per day)
-- DIFFERENCE from 2.2: published_at = when article was written
--                       processed_at = when WE ingested it
SELECT
    DATE(processed_at AT TIME ZONE 'UTC') AS process_date,
    COUNT(*)                               AS article_count
FROM stg_ai_news
WHERE processed_at >= NOW() - INTERVAL '7 days'
GROUP BY process_date
ORDER BY process_date ASC;


-- 2.4 Score Category Distribution
-- Used for: Donut chart showing "Hot Trend" vs "Trending" vs "Normal" split
SELECT
    score_category,
    COUNT(*) AS article_count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 1) AS percentage
FROM stg_ai_news
WHERE score_category IS NOT NULL
GROUP BY score_category
ORDER BY article_count DESC;


-- =============================================================================
-- SECTION 3: Article List Queries (Explorer and Top AI News Pages)
-- =============================================================================

-- 3.1 Latest Articles (Most Recently Published)
-- Used for: News Explorer default view
SELECT
    title,
    source,
    author,
    description,
    published_at,
    url,
    intelligence_score,
    score_category,
    keywords_found,
    processed_at
FROM stg_ai_news
WHERE published_at IS NOT NULL
ORDER BY published_at DESC
LIMIT 20;


-- 3.2 Top Scored Articles (Highest Intelligence Score)
-- Used for: "Top AI News" page — the unique feature of this project
SELECT
    title,
    source,
    description,
    published_at,
    url,
    intelligence_score,
    score_category,
    keywords_found
FROM stg_ai_news
ORDER BY intelligence_score DESC
LIMIT 10;


-- 3.3 Search by Keyword (in title or description)
-- Used for: News Explorer search box
-- Replace 'openai' with your actual search term
-- NOTE: In Python, this uses parameterized queries (not f-strings) for safety
SELECT
    title,
    source,
    description,
    published_at,
    url,
    intelligence_score,
    score_category
FROM stg_ai_news
WHERE LOWER(title)       LIKE '%openai%'
   OR LOWER(description) LIKE '%openai%'
ORDER BY published_at DESC
LIMIT 50;


-- 3.4 Filter by Score Category
-- Used for: News Explorer "Category" filter dropdown
SELECT
    title,
    source,
    published_at,
    url,
    intelligence_score,
    score_category
FROM stg_ai_news
WHERE score_category = 'Trending'   -- Change to: 'Hot Trend', 'High Impact', 'Normal'
ORDER BY intelligence_score DESC
LIMIT 20;


-- 3.5 Articles from a Specific Source
-- Used for: News Explorer "Source" filter dropdown
SELECT
    title,
    description,
    published_at,
    url,
    intelligence_score
FROM stg_ai_news
WHERE LOWER(source) = 'the verge'   -- Replace with any source name
ORDER BY published_at DESC;


-- =============================================================================
-- SECTION 4: Pipeline Health Queries
-- =============================================================================

-- 4.1 Full Pipeline Health Summary
-- Used for: Dashboard "Pipeline Status" section
SELECT
    (SELECT COUNT(*) FROM raw_ai_news)   AS raw_total,
    (SELECT COUNT(*) FROM stg_ai_news)   AS staging_total,
    (SELECT MAX(processed_at) FROM stg_ai_news) AS last_pipeline_run,
    (SELECT ROUND(AVG(intelligence_score), 1) FROM stg_ai_news) AS avg_score;


-- 4.2 Data Quality Check
-- How many articles passed vs failed validation?
-- (All staged articles have is_valid=1 — this confirms data quality)
SELECT
    is_valid,
    COUNT(*) AS article_count
FROM stg_ai_news
GROUP BY is_valid;


-- 4.3 Comparison: Raw vs. Staging Record Count
-- Shows whether all raw articles have been processed into staging
SELECT
    (SELECT COUNT(*) FROM raw_ai_news) AS raw_count,
    (SELECT COUNT(*) FROM stg_ai_news) AS staging_count,
    (SELECT COUNT(*) FROM raw_ai_news) -
    (SELECT COUNT(*) FROM stg_ai_news) AS unprocessed_delta;


-- =============================================================================
-- SECTION 5: Business Insight Queries
-- =============================================================================

-- 5.1 Top AI Companies Mentioned (by article count containing their name)
-- Used for: Insights page "Most Discussed Companies" chart
SELECT
    company,
    COUNT(*) AS mention_count
FROM (
    VALUES
        ('OpenAI'),
        ('Anthropic'),
        ('Google'),
        ('Microsoft'),
        ('NVIDIA'),
        ('Meta'),
        ('Apple'),
        ('Amazon'),
        ('Mistral'),
        ('xAI')
) AS companies(company)
JOIN stg_ai_news s ON (
    LOWER(s.title)       LIKE '%' || LOWER(company) || '%'
    OR LOWER(s.description) LIKE '%' || LOWER(company) || '%'
)
GROUP BY company
ORDER BY mention_count DESC;


-- 5.2 Weekly Article Volume Trend
-- Used for: Understanding how our data collection is growing week over week
SELECT
    DATE_TRUNC('week', published_at AT TIME ZONE 'UTC') AS week_start,
    COUNT(*) AS articles_published
FROM stg_ai_news
WHERE published_at IS NOT NULL
GROUP BY week_start
ORDER BY week_start ASC;


-- 5.3 Average Score by Source (Source Quality Benchmark)
-- Shows which sources consistently produce high-impact AI news
SELECT
    source,
    COUNT(*)                                    AS total_articles,
    ROUND(AVG(intelligence_score), 1)           AS avg_score,
    MAX(intelligence_score)                     AS max_score,
    MIN(intelligence_score)                     AS min_score
FROM stg_ai_news
WHERE source IS NOT NULL AND source != ''
GROUP BY source
HAVING COUNT(*) >= 2
ORDER BY avg_score DESC
LIMIT 15;


-- =============================================================================
-- END OF FILE
-- =============================================================================
