# =============================================================================
# database/warehouse.py — AI Pulse Project
# =============================================================================
#
# PURPOSE:
#   This module handles ALL interactions with the PostgreSQL warehouse:
#     1. Creating the database engine (the connection)
#     2. Creating the table (if it doesn't exist)
#     3. Inserting/upserting records from a Pandas DataFrame
#     4. Providing utility functions for inspection
#
# CONCEPT — What Is a Database Engine?
#   Think of the "engine" as the physical door to the database.
#   SQLAlchemy's create_engine() creates this door using the DATABASE_URL.
#   All database operations (queries, inserts, creates) go through this engine.
#
# CONCEPT — What Is a Session?
#   A "session" is a temporary workspace for database operations.
#   Think of it like a transaction ledger:
#     - You add items to it (session.add)
#     - You commit to save all changes permanently (session.commit)
#     - You rollback to undo changes if something went wrong (session.rollback)
#
# CONCEPT — What Is Upsert?
#   UPSERT = INSERT + UPDATE
#   "Insert the record. If it already exists, update it (or ignore it)."
#   We use INSERT ... ON CONFLICT DO NOTHING for idempotency:
#     - First run: inserts new articles
#     - Second run: skips articles already in the DB (same URL)
#   This is standard Data Engineering practice.
#
# =============================================================================

import pandas as pd                    # DataFrame type for type hints
from sqlalchemy import create_engine, text  # Core SQLAlchemy tools
from sqlalchemy.orm import sessionmaker     # Factory for creating sessions
from sqlalchemy.engine import Engine        # Type for the engine object
from sqlalchemy.dialects.postgresql import insert as pg_insert  # PostgreSQL upsert

# Our project modules
from config.settings import DATABASE_URL, RAW_TABLE_NAME, STG_TABLE_NAME
from database.models import Base, RawAiNews, StagingAiNews
from utils.logger import get_logger

logger = get_logger(__name__)


# =============================================================================
# Engine Creation
# =============================================================================

def create_db_engine() -> Engine:
    """
    Create and return a SQLAlchemy database engine connected to PostgreSQL.

    The engine is the foundation of all database operations.
    It holds the connection pool — a set of pre-established connections
    that can be reused instead of creating a new connection for every query.

    CONCEPT — Connection Pooling:
        Opening a new TCP connection to PostgreSQL is expensive (takes time).
        A "connection pool" keeps a few connections open and ready to use.
        SQLAlchemy manages this automatically — you don't need to worry about it.

    Args:
        None (reads from config.settings)

    Returns:
        Engine: A connected SQLAlchemy engine object.

    Raises:
        Exception: If the database URL is invalid or connection fails.
    """
    logger.info("Creating database engine...")
    logger.debug(f"Connecting to: {DATABASE_URL.split('@')[-1]}")  # Don't log password

    try:
        engine = create_engine(
            DATABASE_URL,
            # echo=False → don't print every SQL statement to console
            # Set to True temporarily if you want to see the raw SQL being executed
            echo=False,
            # pool_size: number of connections to keep open permanently
            pool_size=5,
            # max_overflow: extra connections allowed when pool is full
            max_overflow=10,
            # pool_pre_ping: test connections before using them
            # This detects "stale" connections that were dropped by the server
            pool_pre_ping=True,
        )
        logger.info("Database engine created successfully.")
        return engine

    except Exception as e:
        logger.critical(f"Failed to create database engine: {str(e)}")
        logger.critical("Check your DATABASE_URL in .env file.")
        raise


# =============================================================================
# Table Initialization
# =============================================================================

def initialize_database(engine: Engine) -> None:
    """
    Create all tables defined in models.py if they don't already exist.

    This function is IDEMPOTENT:
      - First run: creates the raw_ai_news table
      - Subsequent runs: does nothing (table already exists)
      - It will NEVER drop or overwrite existing data

    SQLAlchemy handles this with:
      Base.metadata.create_all(engine, checkfirst=True)
      The checkfirst=True tells SQLAlchemy to check if the table exists
      before trying to create it.

    Args:
        engine (Engine): The database engine to create tables in.

    Raises:
        Exception: If table creation fails (e.g., permission denied).
    """
    logger.info("Initializing database schema...")

    try:
        # create_all() inspects all classes that inherit from Base
        # and creates their corresponding tables in the database.
        # checkfirst=True → skip tables that already exist
        Base.metadata.create_all(engine, checkfirst=True)
        logger.info(f"Table '{RAW_TABLE_NAME}' is ready.")

    except Exception as e:
        logger.critical(f"Failed to initialize database: {str(e)}")
        raise


# =============================================================================
# Data Loading
# =============================================================================

def load_dataframe_to_warehouse(df: pd.DataFrame, engine: Engine) -> int:
    """
    Insert records from a Pandas DataFrame into the raw_ai_news table.

    Uses PostgreSQL's INSERT ... ON CONFLICT DO NOTHING pattern for idempotency.
    This means:
      - New articles (URLs not in DB) → inserted
      - Existing articles (same URL) → silently skipped (no error, no update)

    CONCEPT — Why Not Use df.to_sql()?
        Pandas has a built-in df.to_sql() method, but it doesn't support
        ON CONFLICT DO NOTHING. It would either:
          - Fail on duplicate URLs (if_exists='append')
          - Delete ALL existing data first (if_exists='replace')
        By using SQLAlchemy's insert() directly, we get proper upsert behavior.

    Args:
        df (pd.DataFrame): The DataFrame of articles to insert.
        engine (Engine): The database engine.

    Returns:
        int: Number of NEW records actually inserted (duplicates not counted).

    Raises:
        No exceptions are raised — errors are logged and the function returns 0.
    """

    if df is None or df.empty:
        logger.warning("Empty DataFrame received. Nothing to load.")
        return 0

    logger.info(f"Loading {len(df)} records into '{RAW_TABLE_NAME}'...")

    # -------------------------------------------------------------------------
    # Convert DataFrame rows to a list of dictionaries
    # -------------------------------------------------------------------------
    # SQLAlchemy's insert() accepts a list of dicts, where each dict
    # represents one row: {"title": "...", "source": "...", ...}
    #
    # df.to_dict(orient="records") converts:
    #   DataFrame rows → [{"title": "row1"}, {"title": "row2"}, ...]
    # -------------------------------------------------------------------------
    records = df.to_dict(orient="records")

    # -------------------------------------------------------------------------
    # Create a Session (our transaction workspace)
    # -------------------------------------------------------------------------
    # session_factory is callable — calling it gives us a new session.
    # We use 'with' statement so the session is automatically closed
    # even if an exception occurs.
    # -------------------------------------------------------------------------
    session_factory = sessionmaker(bind=engine)

    inserted_count = 0

    with session_factory() as session:
        try:
            # -----------------------------------------------------------------
            # Build the INSERT ... ON CONFLICT DO NOTHING statement
            # -----------------------------------------------------------------
            # This is PostgreSQL-specific syntax:
            #
            #   INSERT INTO raw_ai_news (title, source, ...) VALUES (...)
            #   ON CONFLICT (url) DO NOTHING;
            #
            # "ON CONFLICT (url) DO NOTHING" means:
            #   If a row with the same URL already exists, skip this insert.
            #   Don't raise an error. Don't update. Just skip.
            #
            # This is exactly what we need for idempotency.
            # -----------------------------------------------------------------
            stmt = (
                pg_insert(RawAiNews)         # INSERT INTO raw_ai_news
                .values(records)             # VALUES (all records at once)
                .on_conflict_do_nothing(     # ON CONFLICT DO NOTHING
                    index_elements=["url"]   # ... on the 'url' column
                )
            )

            # Execute the statement within this session
            result = session.execute(stmt)

            # rowcount = number of rows actually inserted (duplicates excluded)
            inserted_count = result.rowcount

            # Commit makes all changes permanent in the database.
            # Without commit(), changes exist only in the session (not saved).
            session.commit()

            skipped = len(records) - inserted_count
            logger.info(f"[OK] Insert complete: {inserted_count} new records inserted, "
                       f"{skipped} duplicates skipped.")

        except Exception as e:
            # If anything goes wrong, rollback undoes all changes in this session.
            # This keeps the database in a consistent state.
            session.rollback()
            logger.error(f"Failed to insert records into {RAW_TABLE_NAME}: {str(e)}")
            logger.error("Transaction rolled back. Database unchanged.")
            return 0

    return inserted_count


# =============================================================================
# Inspection Utility
# =============================================================================

def get_record_count(engine: Engine) -> int:
    """
    Return the total number of records in the raw_ai_news table.

    Used by main.py to report the total size of the warehouse after loading.

    Args:
        engine (Engine): The database engine.

    Returns:
        int: Total row count, or -1 if the query fails.
    """
    try:
        # 'with engine.connect() as conn' opens a connection from the pool
        with engine.connect() as conn:
            # text() wraps a raw SQL string so SQLAlchemy can execute it
            result = conn.execute(text(f"SELECT COUNT(*) FROM {RAW_TABLE_NAME}"))
            count = result.scalar()  # scalar() returns the first column of first row
            return count or 0

    except Exception as e:
        logger.error(f"Could not get record count: {str(e)}")
        return -1


def test_connection(engine: Engine) -> bool:
    """
    Test if the database connection is working.

    SELECT 1 is the simplest possible SQL query — it just returns the number 1.
    If this succeeds, the connection is working. If it fails, something is wrong.

    Args:
        engine (Engine): The database engine to test.

    Returns:
        bool: True if connection is healthy, False otherwise.
    """
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("Database connection test: PASSED [OK]")
        return True

    except Exception as e:
        logger.error(f"Database connection test FAILED: {str(e)}")
        logger.error("Make sure PostgreSQL is running and DATABASE_URL is correct.")
        return False


# =============================================================================
# Week 2 — Staging Layer Functions
# =============================================================================
# These functions are NEW in Week 2. They mirror the pattern established in
# Week 1 (load_dataframe_to_warehouse) but target the stg_ai_news table.
# The existing Week 1 functions above are completely untouched.
# =============================================================================

def load_staging_to_warehouse(df: pd.DataFrame, engine: Engine) -> int:
    """
    Insert scored, validated records into the stg_ai_news staging table.

    Mirrors load_dataframe_to_warehouse() from Week 1, but targets stg_ai_news.
    Uses the same INSERT ... ON CONFLICT DO NOTHING pattern for idempotency:
      - New URLs → inserted
      - Duplicate URLs → silently skipped

    The staging table contains all raw columns PLUS:
      - intelligence_score
      - score_category
      - is_valid
      - validation_notes
      - keywords_found

    Args:
        df (pd.DataFrame):  Scored DataFrame from processing/scorer.py.
                            Must include all stg_ai_news columns.
        engine (Engine):    The database engine.

    Returns:
        int: Number of NEW records actually inserted (duplicates not counted).

    CONCEPT — Why Separate Function?
        Keeping staging load separate from raw load means:
        - We can run them independently (re-process without re-ingesting)
        - Each function has one clear responsibility
        - Easy to add staging-specific logic in Week 3 (e.g., dbt)
    """
    if df is None or df.empty:
        logger.warning("Empty DataFrame passed to load_staging_to_warehouse. Nothing to load.")
        return 0

    logger.info(f"Loading {len(df)} records into '{STG_TABLE_NAME}'...")

    # Only keep columns that exist in the StagingAiNews ORM model
    # This prevents errors if the DataFrame has extra columns (e.g., ingested_at from raw)
    staging_columns = [
        "title", "source", "author", "description", "published_at",
        "url", "category", "intelligence_score", "score_category",
        "is_valid", "validation_notes", "keywords_found",
    ]
    # Filter to only include columns that actually exist in the DataFrame
    available_cols = [col for col in staging_columns if col in df.columns]
    df_to_load = df[available_cols].copy()

    # Convert DataFrame to list of dicts for SQLAlchemy
    records = df_to_load.to_dict(orient="records")

    # Clean each record: replace NaN/NaT with None, convert bool → int
    import math
    cleaned_records = []
    for record in records:
        clean = {}
        for key, value in record.items():
            # pandas NaN and float NaN → None (NULL in PostgreSQL)
            if isinstance(value, float) and math.isnan(value):
                clean[key] = None
            # pandas NaT → None
            elif hasattr(value, '__class__') and value.__class__.__name__ == 'NaTType':
                clean[key] = None
            # Python bool → int (is_valid column is INTEGER in PostgreSQL)
            elif isinstance(value, bool):
                clean[key] = int(value)
            else:
                clean[key] = value
        cleaned_records.append(clean)

    session_factory = sessionmaker(bind=engine)
    inserted_count = 0

    with session_factory() as session:
        try:
            # INSERT INTO stg_ai_news (...) VALUES (...)
            # ON CONFLICT (url) DO NOTHING
            stmt = (
                pg_insert(StagingAiNews)
                .values(cleaned_records)
                .on_conflict_do_nothing(
                    index_elements=["url"]  # Our idempotency key
                )
            )

            result = session.execute(stmt)
            inserted_count = result.rowcount
            session.commit()

            skipped = len(cleaned_records) - inserted_count
            logger.info(
                f"[OK] Staging load complete: {inserted_count} new records inserted, "
                f"{skipped} duplicates skipped."
            )

        except Exception as e:
            session.rollback()
            logger.error(f"Failed to insert records into {STG_TABLE_NAME}: {str(e)}")
            logger.error("Transaction rolled back. Staging table unchanged.")
            return 0

    return inserted_count


def get_staging_record_count(engine: Engine) -> int:
    """
    Return the total number of records in the stg_ai_news staging table.

    Used by main.py to report staging table size after each pipeline run.

    Args:
        engine (Engine): The database engine.

    Returns:
        int: Total row count in stg_ai_news, or -1 if the query fails.
    """
    try:
        with engine.connect() as conn:
            result = conn.execute(text(f"SELECT COUNT(*) FROM {STG_TABLE_NAME}"))
            count = result.scalar()
            return count or 0
    except Exception as e:
        logger.error(f"Could not get staging record count: {str(e)}")
        return -1
