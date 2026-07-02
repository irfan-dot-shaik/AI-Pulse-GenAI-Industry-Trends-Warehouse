# =============================================================================
# analytics/queries.py — AI Pulse Project
# =============================================================================
#
# PURPOSE:
#   Provides Python functions that wrap SQL analytics queries against the
#   stg_ai_news staging table. Each function returns a pandas DataFrame
#   (or a scalar value) and is designed to be called by the Streamlit
#   dashboard pages.
#
# CONCEPT — Why This Layer Exists:
#   In professional data engineering, SQL business logic is never scattered
#   across UI files. It lives in a dedicated "analytics" or "repository"
#   layer. The UI calls functions, not SQL strings. Benefits:
#
#   1. TESTABLE:    Each function can be tested with a mock engine
#   2. REUSABLE:    One function, called by multiple dashboard pages
#   3. READABLE:    Dashboard code has no SQL — just function calls
#   4. MAINTAINABLE: Fix a query in one place, all pages benefit
#
# PATTERN USED — Repository Pattern:
#   This module is an implementation of the "Repository Pattern":
#   The dashboard doesn't know WHERE data comes from (PostgreSQL, CSV, etc.)
#   It only knows WHAT it wants: give me top 10 articles, give me article count.
#   The repository decides how to fetch it.
#
# ALL QUERIES TARGET: stg_ai_news (staging layer)
#   - NOT raw_ai_news (that is the audit trail, not for analytics)
#   - stg_ai_news contains clean, scored, validated articles
#
# =============================================================================

import pandas as pd                          # DataFrame return type
from datetime import datetime, timezone      # For date calculations
from sqlalchemy.engine import Engine         # Type hint for DB engine
from sqlalchemy import text                  # For raw SQL execution

from utils.logger import get_logger          # Centralized logging

logger = get_logger(__name__)

# The staging table we query against (always)
_STAGING_TABLE = "stg_ai_news"


# =============================================================================
# Helper
# =============================================================================

def _safe_query(engine: Engine, sql: str, params: dict = None) -> pd.DataFrame:
    """
    Execute a SQL query safely and return the result as a DataFrame.

    Wraps pd.read_sql_query() with error handling so individual query failures
    don't crash the entire dashboard — they return an empty DataFrame instead.

    Args:
        engine: SQLAlchemy engine connected to ai_pulse_db.
        sql:    Raw SQL string to execute.
        params: Optional dict of bind parameters (for safe parameterization).

    Returns:
        pd.DataFrame: Query results, or empty DataFrame on error.

    CONCEPT — Why pd.read_sql_query?
        pd.read_sql_query() is the bridge between SQL and pandas.
        It runs the query and puts results directly into a DataFrame —
        no manual cursor iteration needed.
    """
    try:
        with engine.connect() as conn:
            if params:
                result = pd.read_sql_query(text(sql), conn, params=params)
            else:
                result = pd.read_sql_query(text(sql), conn)
        return result
    except Exception as e:
        logger.error(f"Analytics query failed: {str(e)}")
        logger.error(f"Query was: {sql[:200]}")
        # Return empty DataFrame so the dashboard can show a graceful empty state
        return pd.DataFrame()


# =============================================================================
# KPI Functions (Used by Dashboard Home Page Cards)
# =============================================================================
# KPI = Key Performance Indicator
# These return single scalar values used for the 4 header cards.
# =============================================================================

def get_total_article_count(engine: Engine) -> int:
    """
    Return the total number of articles in the staging table.

    This is the primary KPI card on the dashboard home page.

    Args:
        engine: SQLAlchemy engine.

    Returns:
        int: Total row count in stg_ai_news.

    SQL:
        SELECT COUNT(*) FROM stg_ai_news
    """
    sql = f"SELECT COUNT(*) AS total FROM {_STAGING_TABLE}"
    df = _safe_query(engine, sql)
    if df.empty:
        return 0
    return int(df["total"].iloc[0])


def get_todays_article_count(engine: Engine) -> int:
    """
    Return the number of articles published today.

    Uses published_at (the article's actual publication date) rather than
    processed_at (when we processed it). This shows today's news volume.

    Args:
        engine: SQLAlchemy engine.

    Returns:
        int: Articles with published_at = today (UTC).

    SQL:
        SELECT COUNT(*) FROM stg_ai_news
        WHERE DATE(published_at AT TIME ZONE 'UTC') = CURRENT_DATE
    """
    sql = f"""
        SELECT COUNT(*) AS total
        FROM {_STAGING_TABLE}
        WHERE DATE(published_at AT TIME ZONE 'UTC') = CURRENT_DATE
    """
    df = _safe_query(engine, sql)
    if df.empty:
        return 0
    return int(df["total"].iloc[0])


def get_unique_source_count(engine: Engine) -> int:
    """
    Return the number of unique news sources in the staging table.

    Tells the user how many different publishers are being tracked.

    Args:
        engine: SQLAlchemy engine.

    Returns:
        int: COUNT(DISTINCT source) from stg_ai_news.

    SQL:
        SELECT COUNT(DISTINCT source) FROM stg_ai_news
    """
    sql = f"SELECT COUNT(DISTINCT source) AS total FROM {_STAGING_TABLE}"
    df = _safe_query(engine, sql)
    if df.empty:
        return 0
    return int(df["total"].iloc[0])


def get_last_updated_time(engine: Engine) -> str:
    """
    Return the timestamp of the most recently processed article.

    Used on the dashboard to show "Last Updated: 2 hours ago".

    Args:
        engine: SQLAlchemy engine.

    Returns:
        str: Formatted string like "2026-07-02 15:30 UTC", or "Never" if empty.

    SQL:
        SELECT MAX(processed_at) FROM stg_ai_news
    """
    sql = f"SELECT MAX(processed_at) AS last_updated FROM {_STAGING_TABLE}"
    df = _safe_query(engine, sql)
    if df.empty or df["last_updated"].iloc[0] is None:
        return "Never"
    ts = df["last_updated"].iloc[0]
    # Format as a readable string
    try:
        if hasattr(ts, 'strftime'):
            return ts.strftime("%Y-%m-%d %H:%M UTC")
        return str(ts)[:16] + " UTC"
    except Exception:
        return str(ts)


def get_average_intelligence_score(engine: Engine) -> float:
    """
    Return the average AI News Intelligence Score across all staged articles.

    Used on the Analytics page as a quality indicator.

    Args:
        engine: SQLAlchemy engine.

    Returns:
        float: Average intelligence_score, rounded to 1 decimal. 0.0 if empty.

    SQL:
        SELECT AVG(intelligence_score) FROM stg_ai_news
    """
    sql = f"SELECT ROUND(AVG(intelligence_score), 1) AS avg_score FROM {_STAGING_TABLE}"
    df = _safe_query(engine, sql)
    if df.empty or df["avg_score"].iloc[0] is None:
        return 0.0
    return float(df["avg_score"].iloc[0])


# =============================================================================
# Chart Data Functions (Used by Analytics and Explorer Pages)
# =============================================================================

def get_articles_per_source(engine: Engine, top_n: int = 10) -> pd.DataFrame:
    """
    Return article counts grouped by news source (top N sources).

    Used to generate the "Top Sources" bar chart on the Analytics page.

    Args:
        engine: SQLAlchemy engine.
        top_n:  Number of top sources to return (default 10).

    Returns:
        pd.DataFrame with columns:
            - source (str):  Publisher name
            - article_count (int): Number of articles from that source

    SQL:
        SELECT source, COUNT(*) AS article_count
        FROM stg_ai_news
        GROUP BY source
        ORDER BY article_count DESC
        LIMIT :n
    """
    sql = f"""
        SELECT
            source,
            COUNT(*) AS article_count
        FROM {_STAGING_TABLE}
        WHERE source IS NOT NULL AND source != ''
        GROUP BY source
        ORDER BY article_count DESC
        LIMIT :n
    """
    return _safe_query(engine, sql, params={"n": top_n})


def get_articles_per_day(engine: Engine, days: int = 30) -> pd.DataFrame:
    """
    Return daily article counts for the last N days.

    Used to generate the "Articles Over Time" line chart.

    Args:
        engine: SQLAlchemy engine.
        days:   Number of days to look back (default 30).

    Returns:
        pd.DataFrame with columns:
            - publish_date (date): Publication date
            - article_count (int): Articles published on that day

    SQL:
        SELECT DATE(published_at) AS publish_date, COUNT(*) AS article_count
        FROM stg_ai_news
        WHERE published_at >= NOW() - INTERVAL ':days days'
        GROUP BY publish_date
        ORDER BY publish_date ASC
    """
    sql = f"""
        SELECT
            DATE(published_at AT TIME ZONE 'UTC') AS publish_date,
            COUNT(*) AS article_count
        FROM {_STAGING_TABLE}
        WHERE published_at >= NOW() - INTERVAL '{days} days'
          AND published_at IS NOT NULL
        GROUP BY publish_date
        ORDER BY publish_date ASC
    """
    return _safe_query(engine, sql)


def get_daily_ingestion_trend(engine: Engine, days: int = 7) -> pd.DataFrame:
    """
    Return daily ingestion counts (when WE processed articles) for the last N days.

    This is different from get_articles_per_day():
      - get_articles_per_day()    → when articles were PUBLISHED
      - get_daily_ingestion_trend() → when WE INGESTED/PROCESSED them

    Used to generate the "Pipeline Activity" trend chart on the Analytics page.

    Args:
        engine: SQLAlchemy engine.
        days:   Number of days to look back (default 7).

    Returns:
        pd.DataFrame with columns:
            - process_date (date): Date we processed the articles
            - article_count (int): How many articles we processed that day

    SQL:
        SELECT DATE(processed_at) AS process_date, COUNT(*) AS article_count
        FROM stg_ai_news
        WHERE processed_at >= NOW() - INTERVAL ':days days'
        GROUP BY process_date
        ORDER BY process_date ASC
    """
    sql = f"""
        SELECT
            DATE(processed_at AT TIME ZONE 'UTC') AS process_date,
            COUNT(*) AS article_count
        FROM {_STAGING_TABLE}
        WHERE processed_at >= NOW() - INTERVAL '{days} days'
        GROUP BY process_date
        ORDER BY process_date ASC
    """
    return _safe_query(engine, sql)


def get_score_category_distribution(engine: Engine) -> pd.DataFrame:
    """
    Return article counts broken down by intelligence score category.

    Used for the donut/pie chart on the Analytics page showing the
    distribution of "Hot Trend" vs "High Impact" vs "Trending" vs "Normal".

    Args:
        engine: SQLAlchemy engine.

    Returns:
        pd.DataFrame with columns:
            - score_category (str):  Category label
            - article_count (int):   Number of articles in that category

    SQL:
        SELECT score_category, COUNT(*) AS article_count
        FROM stg_ai_news
        GROUP BY score_category
        ORDER BY article_count DESC
    """
    sql = f"""
        SELECT
            score_category,
            COUNT(*) AS article_count
        FROM {_STAGING_TABLE}
        WHERE score_category IS NOT NULL
        GROUP BY score_category
        ORDER BY article_count DESC
    """
    return _safe_query(engine, sql)


# =============================================================================
# Article List Functions (Used by Explorer and Top AI News Pages)
# =============================================================================

def get_latest_articles(engine: Engine, limit: int = 20) -> pd.DataFrame:
    """
    Return the most recently published articles.

    Used by the News Explorer page as the default listing.

    Args:
        engine: SQLAlchemy engine.
        limit:  Number of articles to return (default 20).

    Returns:
        pd.DataFrame with columns:
            title, source, description, published_at, url,
            intelligence_score, score_category, keywords_found

    SQL:
        SELECT ... FROM stg_ai_news ORDER BY published_at DESC LIMIT :n
    """
    sql = f"""
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
        FROM {_STAGING_TABLE}
        WHERE published_at IS NOT NULL
        ORDER BY published_at DESC
        LIMIT :n
    """
    return _safe_query(engine, sql, params={"n": limit})


def get_top_scored_articles(engine: Engine, limit: int = 10) -> pd.DataFrame:
    """
    Return articles with the highest AI News Intelligence Score.

    Used by the "Top AI News" page to show the most impactful articles.

    Args:
        engine: SQLAlchemy engine.
        limit:  Number of top articles to return (default 10).

    Returns:
        pd.DataFrame ordered by intelligence_score DESC.

    SQL:
        SELECT ... FROM stg_ai_news ORDER BY intelligence_score DESC LIMIT :n
    """
    sql = f"""
        SELECT
            title,
            source,
            description,
            published_at,
            url,
            intelligence_score,
            score_category,
            keywords_found
        FROM {_STAGING_TABLE}
        ORDER BY intelligence_score DESC
        LIMIT :n
    """
    return _safe_query(engine, sql, params={"n": limit})


def search_articles(
    engine: Engine,
    keyword: str = "",
    source_filter: str = "",
    score_filter: str = "",
    sort_by: str = "newest",
    limit: int = 50,
) -> pd.DataFrame:
    """
    Search and filter articles with flexible criteria.

    Used by the News Explorer page for the search + filter functionality.

    Args:
        engine:       SQLAlchemy engine.
        keyword:      Search term to match in title or description (case-insensitive).
        source_filter: Filter to articles from this specific source.
        score_filter: Filter by score category ("Hot Trend", "High Impact", etc.)
        sort_by:      "newest" (by published_at DESC),
                      "oldest" (by published_at ASC),
                      "score"  (by intelligence_score DESC)
        limit:        Max rows to return (default 50).

    Returns:
        pd.DataFrame matching the search criteria.

    CONCEPT — Parameterized Queries:
        We use :keyword (SQLAlchemy bind parameter) instead of f-string
        interpolation for the keyword value. This prevents SQL injection.
        Never put user input directly into a SQL string!

        Safe:   WHERE LOWER(title) LIKE :keyword  (params={"keyword": "%gpt%"})
        UNSAFE: WHERE LOWER(title) LIKE '%{keyword}%'  <- SQL injection risk!
    """
    # Build the WHERE clause conditions
    conditions = ["1=1"]  # Always-true base condition for easy AND chaining
    params = {"limit": limit}

    if keyword:
        conditions.append("(LOWER(title) LIKE :kw OR LOWER(description) LIKE :kw)")
        params["kw"] = f"%{keyword.lower()}%"

    if source_filter:
        conditions.append("LOWER(source) = :src")
        params["src"] = source_filter.lower()

    if score_filter:
        conditions.append("score_category = :cat")
        params["cat"] = score_filter

    where_clause = " AND ".join(conditions)

    # Build ORDER BY clause
    order_map = {
        "newest": "published_at DESC",
        "oldest": "published_at ASC",
        "score":  "intelligence_score DESC",
    }
    order_by = order_map.get(sort_by, "published_at DESC")

    sql = f"""
        SELECT
            title,
            source,
            author,
            description,
            published_at,
            url,
            intelligence_score,
            score_category,
            keywords_found
        FROM {_STAGING_TABLE}
        WHERE {where_clause}
        ORDER BY {order_by}
        LIMIT :limit
    """
    return _safe_query(engine, sql, params=params)


def get_all_sources(engine: Engine) -> list[str]:
    """
    Return a sorted list of all unique source names in the staging table.

    Used to populate the source filter dropdown in the News Explorer.

    Args:
        engine: SQLAlchemy engine.

    Returns:
        list[str]: Alphabetically sorted list of source names.
    """
    sql = f"""
        SELECT DISTINCT source
        FROM {_STAGING_TABLE}
        WHERE source IS NOT NULL AND source != ''
        ORDER BY source ASC
    """
    df = _safe_query(engine, sql)
    if df.empty:
        return []
    return df["source"].tolist()


# =============================================================================
# Pipeline Health Function (Used by Dashboard Status Bar)
# =============================================================================

def get_pipeline_health(engine: Engine) -> dict:
    """
    Return a health summary of the pipeline and both database tables.

    Used to populate the "Pipeline Status" section on the dashboard home page.

    Args:
        engine: SQLAlchemy engine.

    Returns:
        dict with keys:
            - raw_count (int):     Total rows in raw_ai_news
            - staging_count (int): Total rows in stg_ai_news
            - last_run (str):      Most recent processed_at timestamp
            - db_connected (bool): Whether the DB is reachable
            - avg_score (float):   Average intelligence score

    CONCEPT — Health Checks:
        Production systems always expose health endpoints.
        This function is our health endpoint — it tells the dashboard
        whether everything is working before rendering data.
    """
    health = {
        "raw_count":     0,
        "staging_count": 0,
        "last_run":      "Never",
        "db_connected":  False,
        "avg_score":     0.0,
    }

    try:
        # Test connection first
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        health["db_connected"] = True

        # Raw table count
        raw_df = _safe_query(engine, "SELECT COUNT(*) AS cnt FROM raw_ai_news")
        if not raw_df.empty:
            health["raw_count"] = int(raw_df["cnt"].iloc[0])

        # Staging table count
        stg_df = _safe_query(engine, f"SELECT COUNT(*) AS cnt FROM {_STAGING_TABLE}")
        if not stg_df.empty:
            health["staging_count"] = int(stg_df["cnt"].iloc[0])

        # Last pipeline run
        health["last_run"] = get_last_updated_time(engine)

        # Average score
        health["avg_score"] = get_average_intelligence_score(engine)

    except Exception as e:
        logger.error(f"Pipeline health check failed: {str(e)}")
        health["db_connected"] = False

    return health


# =============================================================================
# Keyword Frequency Function (Used by Insights Page)
# =============================================================================

def get_keyword_frequency(engine: Engine, top_n: int = 15) -> pd.DataFrame:
    """
    Return the most frequently mentioned AI keywords across all staged articles.

    This function fetches the keywords_found column (comma-separated strings)
    and aggregates them on the Python side, since PostgreSQL's string splitting
    would be more complex and less portable.

    Args:
        engine: SQLAlchemy engine.
        top_n:  Number of top keywords to return.

    Returns:
        pd.DataFrame with columns:
            - keyword (str):    The AI keyword
            - frequency (int):  How many articles mention it

    CONCEPT — Python-Side Aggregation:
        Sometimes it's easier to fetch raw data into Python and aggregate
        there. This is a valid pattern when the SQL equivalent would be
        overly complex. For production scale, this would move to SQL/dbt.
    """
    sql = f"""
        SELECT keywords_found
        FROM {_STAGING_TABLE}
        WHERE keywords_found IS NOT NULL AND keywords_found != ''
    """
    df = _safe_query(engine, sql)

    if df.empty:
        return pd.DataFrame(columns=["keyword", "frequency"])

    # Count individual keyword occurrences
    keyword_counts: dict[str, int] = {}
    for kw_string in df["keywords_found"]:
        if not kw_string:
            continue
        for kw in kw_string.split(","):
            kw = kw.strip().lower()
            if kw:
                keyword_counts[kw] = keyword_counts.get(kw, 0) + 1

    if not keyword_counts:
        return pd.DataFrame(columns=["keyword", "frequency"])

    # Convert to DataFrame and sort by frequency
    result_df = pd.DataFrame(
        list(keyword_counts.items()),
        columns=["keyword", "frequency"]
    )
    result_df = result_df.sort_values("frequency", ascending=False).head(top_n)
    result_df = result_df.reset_index(drop=True)

    return result_df


# =============================================================================
# Publisher Performance (Module 5 — Analytics Page)
# =============================================================================

def get_publisher_performance(engine: Engine, min_articles: int = 1) -> pd.DataFrame:
    """
    Return a ranked publisher performance table for the Analytics page.

    Columns: source, article_count, avg_score, max_score, min_score.
    Ordered by article_count DESC, then avg_score DESC.

    Args:
        engine:       SQLAlchemy engine.
        min_articles: Minimum article count to include a source (default 1).

    Returns:
        pd.DataFrame with publisher performance metrics.
    """
    sql = f"""
        SELECT
            source,
            COUNT(*)                                AS article_count,
            ROUND(AVG(intelligence_score), 1)       AS avg_score,
            MAX(intelligence_score)                 AS max_score,
            MIN(intelligence_score)                 AS min_score
        FROM {_STAGING_TABLE}
        WHERE source IS NOT NULL AND source != ''
        GROUP BY source
        HAVING COUNT(*) >= :min_articles
        ORDER BY article_count DESC, avg_score DESC
    """
    return _safe_query(engine, sql, params={"min_articles": min_articles})


def get_max_intelligence_score(engine: Engine) -> int:
    """
    Return the single highest intelligence score in the staging table.

    Used for the "Peak Score" KPI card on the Analytics page.

    Args:
        engine: SQLAlchemy engine.

    Returns:
        int: Maximum intelligence_score value, or 0 if table is empty.
    """
    sql = f"SELECT MAX(intelligence_score) AS peak FROM {_STAGING_TABLE}"
    df = _safe_query(engine, sql)
    if df.empty or df["peak"].iloc[0] is None:
        return 0
    return int(df["peak"].iloc[0])


# =============================================================================
# Company Mentions (Module 6 — Top AI News page)
# =============================================================================

# Canonical AI company name variants → display name
_COMPANY_ALIASES: dict[str, str] = {
    "openai": "OpenAI", "gpt": "OpenAI", "chatgpt": "OpenAI",
    "google": "Google", "gemini": "Google", "deepmind": "Google",
    "anthropic": "Anthropic", "claude": "Anthropic",
    "nvidia": "NVIDIA", "cuda": "NVIDIA",
    "microsoft": "Microsoft", "copilot": "Microsoft", "azure": "Microsoft",
    "meta": "Meta", "llama": "Meta",
    "amazon": "Amazon", "aws": "Amazon", "bedrock": "Amazon",
    "apple": "Apple",
    "mistral": "Mistral",
    "hugging face": "Hugging Face", "huggingface": "Hugging Face",
}

_DISPLAY_ORDER = ["OpenAI", "Google", "Microsoft", "Anthropic",
                  "NVIDIA", "Meta", "Amazon", "Apple", "Mistral", "Hugging Face"]


def get_company_mentions(engine: Engine) -> pd.DataFrame:
    """
    Aggregate keyword_found column to count AI company mentions.

    Maps keyword variants (e.g. "gpt", "chatgpt") → canonical company name
    (e.g. "OpenAI"). Returns a DataFrame sorted by mention count DESC.

    Args:
        engine: SQLAlchemy engine.

    Returns:
        pd.DataFrame with columns ['company', 'mentions'].
    """
    sql = f"SELECT keywords_found FROM {_STAGING_TABLE} WHERE keywords_found IS NOT NULL"
    df = _safe_query(engine, sql)
    if df.empty:
        return pd.DataFrame(columns=["company", "mentions"])

    counts: dict[str, int] = {}
    for kw_str in df["keywords_found"].dropna():
        for kw in str(kw_str).split(","):
            kw = kw.strip().lower()
            company = _COMPANY_ALIASES.get(kw)
            if company:
                counts[company] = counts.get(company, 0) + 1

    if not counts:
        return pd.DataFrame(columns=["company", "mentions"])

    rows = [{"company": c, "mentions": counts[c]}
            for c in _DISPLAY_ORDER if c in counts]
    # Append any companies not in display order
    for c, m in counts.items():
        if c not in _DISPLAY_ORDER:
            rows.append({"company": c, "mentions": m})

    result = pd.DataFrame(rows).sort_values("mentions", ascending=False)
    return result.reset_index(drop=True)
