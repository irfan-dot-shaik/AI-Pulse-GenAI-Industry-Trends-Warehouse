# =============================================================================
# dashboard/utils/db_helper.py — AI Pulse Dashboard
# =============================================================================
#
# PURPOSE:
#   Provides a cached SQLAlchemy engine for the Streamlit dashboard.
#
# CONCEPT — @st.cache_resource:
#   Streamlit re-runs the entire Python script on EVERY user interaction
#   (button click, slider move, page load). Without caching, this would
#   create a NEW database connection on every single interaction — extremely
#   wasteful and potentially exhausting the connection pool.
#
#   @st.cache_resource solves this:
#     - The function runs ONCE on first call
#     - The engine object is stored in Streamlit's cache
#     - Every subsequent call returns the SAME cached engine
#     - The cache is shared across ALL pages in the multipage app
#
#   This is the Streamlit-recommended pattern for database connections.
#
# CONCEPT — Why not import engine from main.py?
#   main.py is the pipeline entry point — it's not meant to be imported.
#   The dashboard has its own engine creation via this helper.
#   Both use the same DATABASE_URL from config/settings.py.
#
# =============================================================================

import sys
import os

# Add project root to Python path so we can import project modules
# This is needed because Streamlit runs from the dashboard/ directory
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

import streamlit as st                        # For @st.cache_resource
from sqlalchemy.engine import Engine          # Type hint
from database.warehouse import create_db_engine  # Our Week 1 engine factory


@st.cache_resource(show_spinner="Connecting to database...")
def get_engine() -> Engine:
    """
    Create and cache the SQLAlchemy database engine.

    This function is decorated with @st.cache_resource, which means:
    - It runs exactly ONCE per Streamlit session
    - The engine is reused for ALL subsequent calls
    - All dashboard pages share the same connection pool

    Returns:
        Engine: A connected SQLAlchemy engine, or None if connection fails.

    USAGE in any dashboard page:
        from dashboard.utils.db_helper import get_engine
        engine = get_engine()
        if engine is None:
            st.error("Database not connected.")
            st.stop()
    """
    try:
        engine = create_db_engine()
        return engine
    except Exception:
        # Return None — dashboard pages check for None and show an error state
        return None


def is_db_connected(engine: Engine) -> bool:
    """
    Test whether the database connection is live.

    Used by the sidebar to show a green/red connection status dot.

    Args:
        engine: SQLAlchemy engine from get_engine().

    Returns:
        bool: True if DB responds to SELECT 1, False otherwise.
    """
    if engine is None:
        return False
    try:
        from sqlalchemy import text
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
