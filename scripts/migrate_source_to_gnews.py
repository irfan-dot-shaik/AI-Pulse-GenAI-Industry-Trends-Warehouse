"""
scripts/migrate_source_to_gnews.py — AI Pulse Project
=======================================================

PURPOSE:
    One-time data migration to fix historical records in both raw_ai_news
    and stg_ai_news where the 'source' column contains publisher names
    (e.g., "TechCrunch", "Reuters", "CNBC") instead of the ingestion system
    name "GNews".

WHY THIS IS NEEDED:
    Before Week 3, gnews_client.py set source = article["source"]["name"]
    (the publisher outlet name). This was correct for Week 1/2, but in
    Week 3 the 'source' column represents the INGESTION PIPELINE, not the
    publisher. Hacker News sets source = "Hacker News" and Reddit sets
    source = "Reddit/<subreddit>", so GNews must set source = "GNews" for
    the Source Analytics page to work correctly.

WHAT THIS SCRIPT DOES:
    1. Identifies all rows in raw_ai_news where source is NOT one of the
       known ingestion system names.
    2. Updates those rows: source → "GNews" (since all legacy data came
       from GNews).
    3. Does the same for stg_ai_news.
    4. Prints a summary of rows updated.

SAFE TO RUN:
    - Uses UPDATE ... WHERE source NOT IN (...) — only touches legacy rows
    - Idempotent: running it twice has no additional effect
    - Hacker News and Reddit rows are NOT touched (their source values are
      already correct: "Hacker News", "Reddit/MachineLearning", etc.)

USAGE:
    python scripts/migrate_source_to_gnews.py
"""

import sys
import os

# Add project root to path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from database.warehouse import create_db_engine
from utils.logger import get_logger

logger = get_logger(__name__)

# These are the known ingestion system names — rows with these values are CORRECT
# and must NOT be touched.
KNOWN_INGESTION_SOURCES = [
    "GNews",
    "Hacker News",
    "Reddit/MachineLearning",
    "Reddit/artificial",
    "Reddit/singularity",
]

# SQL placeholder list — "('GNews', 'Hacker News', ...)"
_IN_LIST = ", ".join(f"'{s}'" for s in KNOWN_INGESTION_SOURCES)


def migrate_table(engine, table_name: str) -> int:
    """
    Update source = 'GNews' for all rows in table_name where source is not
    one of the known ingestion system names.

    Returns:
        int: Number of rows updated.
    """
    sql = text(f"""
        UPDATE {table_name}
        SET source = 'GNews'
        WHERE source NOT IN ({_IN_LIST})
           OR source IS NULL
    """)

    with engine.begin() as conn:
        result = conn.execute(sql)
        return result.rowcount


def main():
    print("=" * 60)
    print("AI Pulse -- Source Column Migration")
    print("Backfilling legacy GNews publisher names -> 'GNews'")
    print("=" * 60)

    engine = create_db_engine()

    for table in ["raw_ai_news", "stg_ai_news"]:
        print(f"\n[{table}] Checking for legacy publisher-name records...")
        updated = migrate_table(engine, table)
        if updated > 0:
            print(f"[{table}] DONE: Updated {updated} rows: source -> 'GNews'")
        else:
            print(f"[{table}] DONE: No legacy rows found -- already clean")

    print("\n" + "=" * 60)
    print("Migration complete.")
    print("Next step: run 'python main.py' to ingest fresh data,")
    print("then open the Source Analytics dashboard page.")
    print("=" * 60)


if __name__ == "__main__":
    main()
