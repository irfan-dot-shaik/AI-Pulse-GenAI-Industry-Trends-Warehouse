# =============================================================================
# main.py — AI Pulse Project
# =============================================================================
#
# PROJECT:  AI Pulse – GenAI Industry Trends Warehouse
# AUTHOR:   AI Pulse Data Engineering Team
# WEEK:     1 — Foundation + Architecture
#
# PURPOSE:
#   This is the ENTRY POINT for the entire data pipeline.
#   It orchestrates the following steps in sequence:
#
#   Step 1: Validate configuration (API key, DB URL)
#   Step 2: Test database connection
#   Step 3: Initialize the database schema (create table if not exists)
#   Step 4: Fetch AI news articles from GNews API
#   Step 5: Load articles into PostgreSQL raw layer
#   Step 6: Report pipeline run summary
#
# CONCEPT — Orchestrator Pattern:
#   main.py does NOT contain any business logic.
#   It imports functions from other modules and calls them in order.
#   This is the "Orchestrator" design pattern:
#     - ingestion/gnews_client.py → knows how to fetch data
#     - database/warehouse.py     → knows how to save data
#     - main.py                   → coordinates the two
#
#   This separation makes it easy to:
#     - Replace GNews with Reddit in Week 3 (just swap the ingestion module)
#     - Add more steps (transform, validate) between fetch and load
#     - Schedule this file with cron or Airflow in later weeks
#
# HOW TO RUN:
#   From the project root:
#   python main.py
#
# EXPECTED OUTPUT (when working):
#   2026-06-24 18:30:01 | main | INFO     | =============================
#   2026-06-24 18:30:01 | main | INFO     | AI Pulse Data Pipeline — Week 1
#   2026-06-24 18:30:01 | main | INFO     | =============================
#   2026-06-24 18:30:02 | main | INFO     | ✓ Config validated
#   2026-06-24 18:30:03 | main | INFO     | ✓ Database connection healthy
#   2026-06-24 18:30:03 | main | INFO     | ✓ Schema initialized
#   2026-06-24 18:30:05 | main | INFO     | ✓ Fetched 10 articles from GNews
#   2026-06-24 18:30:06 | main | INFO     | ✓ Inserted 10 new records (0 duplicates)
#   2026-06-24 18:30:06 | main | INFO     | ✓ Total records in warehouse: 10
#
# =============================================================================

import sys                      # For sys.exit() — cleanly exits with an error code
from datetime import datetime, timezone  # For timing the pipeline run
import pandas as pd             # For pd.concat (multi-source merge)

# --- Project modules ---
# We import from our own modules using the package.module.function pattern
from config.settings import (
    validate_config,
    REDDIT_CLIENT_ID,
    REDDIT_CLIENT_SECRET,
    HN_FETCH_LIMIT,
)
from ingestion.gnews_client import fetch_ai_news
from ingestion.hn_client import fetch_hn_news           # Week 3: Hacker News
from ingestion.reddit_client import fetch_reddit_news   # Week 3: Reddit (optional)
from database.warehouse import (
    create_db_engine,
    initialize_database,
    load_dataframe_to_warehouse,
    get_record_count,
    test_connection,
)
from utils.logger import get_logger

# Create a logger for this module
# __name__ = "main" when this file is run directly
logger = get_logger(__name__)


# =============================================================================
# Pipeline Banner
# =============================================================================

BANNER = """
==============================================================
   AI PULSE -- GenAI Industry Trends Warehouse
   Data Pipeline -- Week 1 + 2 + 3
   GNews + HackerNews + Reddit -> Validate -> Score -> PostgreSQL
=============================================================="""


# =============================================================================
# Main Pipeline Function
# =============================================================================

def run_pipeline() -> None:
    """
    Execute the complete data pipeline end-to-end (Week 1 + Week 2 + Week 3).

    Pipeline Steps:
        1. Validate configuration
        2. Establish database connection
        3. Initialize database schema (raw + staging tables)
        4. Fetch news from ALL sources (GNews + HackerNews + Reddit)
        5. Load raw articles into raw_ai_news (Week 1)
        6. Validate, transform, score -> load to stg_ai_news (Week 2)
        7. Report summary

    This function raises SystemExit on fatal errors so the caller
    (or a scheduler in later weeks) can detect pipeline failures.
    """

    # Record when the pipeline started (for reporting run duration)
    pipeline_start = datetime.now(timezone.utc)

    # Print the startup banner to console
    print(BANNER)
    logger.info("Pipeline execution started")

    # =========================================================================
    # STEP 1: Validate Configuration
    # =========================================================================
    # Before doing anything, check that required env vars are set.
    # "Fail fast" — catch problems at startup, not halfway through.
    # =========================================================================
    logger.info("-" * 60)
    logger.info("STEP 1/6 -- Validating configuration")
    logger.info("-" * 60)

    try:
        validate_config()
        logger.info("[OK] All required environment variables are present")
    except ValueError as e:
        logger.critical(f"Configuration error: {str(e)}")
        logger.critical("Pipeline aborted. Fix your .env file and retry.")
        sys.exit(1)  # Exit code 1 = error (0 = success in Unix conventions)

    # =========================================================================
    # STEP 2: Establish Database Connection
    # =========================================================================
    logger.info("-" * 60)
    logger.info("STEP 2/6 -- Connecting to PostgreSQL")
    logger.info("-" * 60)

    try:
        # create_db_engine() builds the connection pool
        engine = create_db_engine()
    except Exception as e:
        logger.critical(f"Cannot create database engine: {str(e)}")
        sys.exit(1)

    # test_connection() sends a SELECT 1 to verify the DB is reachable
    if not test_connection(engine):
        logger.critical("Cannot reach PostgreSQL. Pipeline aborted.")
        logger.critical("Troubleshooting checklist:")
        logger.critical("  1. Is PostgreSQL service running? (Check Services in Windows)")
        logger.critical("  2. Is DATABASE_URL correct in your .env file?")
        logger.critical("  3. Does the database 'ai_pulse_db' exist?")
        logger.critical("     Run: psql -U postgres -c 'CREATE DATABASE ai_pulse_db;'")
        sys.exit(1)

    logger.info("[OK] Successfully connected to PostgreSQL")

    # =========================================================================
    # STEP 3: Initialize Database Schema
    # =========================================================================
    # Creates the raw_ai_news table if it doesn't already exist.
    # Safe to run on every pipeline execution (idempotent).
    # =========================================================================
    logger.info("-" * 60)
    logger.info("STEP 3/6 -- Initializing database schema")
    logger.info("-" * 60)

    try:
        initialize_database(engine)
        logger.info("[OK] Table 'raw_ai_news' is ready")
    except Exception as e:
        logger.critical(f"Schema initialization failed: {str(e)}")
        sys.exit(1)

    # =========================================================================
    # STEP 4: Fetch Data from ALL Sources (Week 3 — Multi-Source)
    # =========================================================================
    # CONCEPT — Multi-Source Merge:
    #   Each source client returns an Optional[pd.DataFrame] with the same
    #   7-column schema. We collect all non-None DataFrames and merge them
    #   with pd.concat(). The merged DataFrame then flows through the
    #   UNCHANGED Steps 5 and 6 (validation, transform, score, load).
    #
    #   Sources:
    #     GNews     — always runs (requires GNEWS_API_KEY)
    #     HackerNews — always runs (no auth needed)
    #     Reddit    — runs only if REDDIT_CLIENT_ID + SECRET are in .env
    # =========================================================================
    logger.info("-" * 60)
    logger.info("STEP 4/6 -- Multi-source fetch (GNews + HackerNews + Reddit)")
    logger.info("-" * 60)

    all_frames: list[pd.DataFrame] = []
    source_counts: dict[str, int] = {}

    # --- Source 1: GNews (always run) ---
    logger.info("[Source 1/3] GNews API...")
    gnews_df = fetch_ai_news()
    if gnews_df is not None:
        all_frames.append(gnews_df)
        source_counts["GNews"] = len(gnews_df)
        logger.info(f"[GNews] {len(gnews_df)} articles collected")
    else:
        logger.warning("[GNews] Returned no data. Check GNEWS_API_KEY and network.")
        source_counts["GNews"] = 0

    # --- Source 2: Hacker News (always run, no auth) ---
    logger.info("[Source 2/3] Hacker News (top/best/new feeds)...")
    hn_df = fetch_hn_news(limit=HN_FETCH_LIMIT)
    if hn_df is not None:
        all_frames.append(hn_df)
        source_counts["Hacker News"] = len(hn_df)
        logger.info(f"[HN] {len(hn_df)} articles collected")
    else:
        logger.warning("[HN] No AI-relevant articles found.")
        source_counts["Hacker News"] = 0

    # --- Source 3: Reddit (optional — skips gracefully if credentials absent) ---
    logger.info("[Source 3/3] Reddit (PRAW)...")
    if REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET:
        reddit_df = fetch_reddit_news()
        if reddit_df is not None:
            all_frames.append(reddit_df)
            source_counts["Reddit"] = len(reddit_df)
            logger.info(f"[Reddit] {len(reddit_df)} articles collected")
        else:
            logger.warning("[Reddit] No external articles found.")
            source_counts["Reddit"] = 0
    else:
        logger.info(
            "[Reddit] Skipped — REDDIT_CLIENT_ID / REDDIT_CLIENT_SECRET not set in .env. "
            "Add them to enable Reddit ingestion."
        )
        source_counts["Reddit"] = 0

    # --- Log source breakdown ---
    logger.info("[Multi-source summary]:")
    for src, cnt in source_counts.items():
        logger.info(f"  {src}: {cnt} articles")

    # --- Abort if ALL sources returned nothing ---
    if not all_frames:
        logger.error("All sources returned no data. Pipeline completing with 0 records.")
        _report_summary(pipeline_start, fetched=0, inserted=0, staging_inserted=0, engine=engine)
        return

    # --- Merge all source DataFrames into one ---
    df = pd.concat(all_frames, ignore_index=True)
    logger.info(f"[OK] Total articles merged: {len(df)} from {len(all_frames)} source(s)")

    # Log a sample of what we fetched (first 3 titles across all sources)
    logger.info("Sample articles fetched:")
    for i, row in df.head(3).iterrows():
        logger.info(f"  [{i+1}] [{row.get('source', '?')}] {row['title'][:65]}...")

    # =========================================================================
    # STEP 5: Load Data into PostgreSQL
    # =========================================================================
    logger.info("-" * 60)
    logger.info("STEP 5/6 -- Loading raw articles into PostgreSQL")
    logger.info("-" * 60)

    inserted = load_dataframe_to_warehouse(df, engine)

    # =========================================================================
    # STEP 6: Process and Load to Staging Layer (Week 2)
    # =========================================================================
    # This is the new Week 2 step. It takes the fetched articles and:
    #   1. Validates them (removes incomplete records)
    #   2. Transforms them (normalizes text)
    #   3. Scores them (computes AI Intelligence Score 0-100)
    #   4. Loads the results into stg_ai_news
    # =========================================================================
    logger.info("-" * 60)
    logger.info("STEP 6/6 -- Processing and loading to staging layer")
    logger.info("-" * 60)

    # Import processing modules (done here to keep Week 1 imports clean at top)
    from processing.validator import validate_articles
    from processing.transformer import transform_articles
    from processing.scorer import score_articles
    from database.warehouse import load_staging_to_warehouse, get_staging_record_count

    # Step 6a: Validate — remove articles with missing title, URL, or timestamp
    validation_result = validate_articles(df)
    logger.info(
        f"Validation: {validation_result.report['valid']} valid, "
        f"{validation_result.report['invalid']} invalid articles"
    )

    staging_inserted = 0
    if validation_result.valid_df.empty:
        logger.warning("No valid articles to process. Staging table not updated.")
    else:
        # Step 6b: Transform — normalize and clean the valid articles
        transformed_df = transform_articles(validation_result.valid_df)

        # Step 6c: Score — compute AI Intelligence Score for each article
        scored_df = score_articles(transformed_df)

        # Step 6d: Load — insert scored articles into stg_ai_news
        staging_inserted = load_staging_to_warehouse(scored_df, engine)

        logger.info(f"[OK] Staging layer updated: {staging_inserted} new records")

    staging_total = get_staging_record_count(engine)
    logger.info(f"Total records in stg_ai_news: {staging_total}")

    # =========================================================================
    # STEP 7: Report Summary
    # =========================================================================
    _report_summary(
        pipeline_start,
        fetched=len(df),
        inserted=inserted,
        staging_inserted=staging_inserted,
        engine=engine
    )


def _report_summary(
    pipeline_start: datetime,
    fetched: int,
    inserted: int,
    staging_inserted: int,
    engine
) -> None:
    """
    Log a formatted summary of the pipeline run.

    Args:
        pipeline_start:    When the pipeline started (UTC datetime)
        fetched:           Number of articles fetched from API
        inserted:          Number of new records inserted to raw_ai_news
        staging_inserted:  Number of new records inserted to stg_ai_news
        engine:            DB engine for getting total record count
    """
    pipeline_end = datetime.now(timezone.utc)
    duration_seconds = (pipeline_end - pipeline_start).total_seconds()

    total_in_db = get_record_count(engine)
    duplicates_skipped = fetched - inserted if fetched > 0 else 0

    # Import here to avoid circular import concerns
    from database.warehouse import get_staging_record_count
    staging_total = get_staging_record_count(engine)

    summary = f"""
==============================================================
              PIPELINE RUN SUMMARY (Week 1 + 2)
==============================================================
  Status:              SUCCESS
  Run Duration:        {f"{duration_seconds:.2f}s"}
  Articles Fetched:    {fetched}
  Raw New Records:     {inserted}
  Raw Duplicates:      {duplicates_skipped}
  Raw Total in DB:     {total_in_db}
  Staging New:         {staging_inserted}
  Staging Total:       {staging_total}
==============================================================
"""
    print(summary)
    logger.info("Pipeline execution completed successfully")
    logger.info(
        f"Duration: {duration_seconds:.2f}s | "
        f"Fetched: {fetched} | "
        f"Raw inserted: {inserted} | "
        f"Staging inserted: {staging_inserted} | "
        f"Raw total: {total_in_db} | "
        f"Staging total: {staging_total}"
    )


# =============================================================================
# Entry Point Guard
# =============================================================================
# CONCEPT — if __name__ == "__main__":
#   When Python runs a file directly (python main.py), it sets __name__ = "__main__".
#   When a file is imported by another module, __name__ = the module name.
#
#   This guard ensures run_pipeline() only executes when YOU run the file,
#   not when pytest or another module imports it.
#
#   Without this guard, importing from main.py would run the entire pipeline!
# =============================================================================

if __name__ == "__main__":
    run_pipeline()
