# =============================================================================
# analytics/__init__.py — AI Pulse Project
# =============================================================================
#
# PURPOSE:
#   Makes 'analytics' a Python package so you can import from it:
#     from analytics.queries import get_top_scored_articles
#
# CONCEPT — Why a Separate Analytics Module?
#   The dashboard (Streamlit) should NEVER contain raw SQL strings.
#   Mixing SQL with UI code violates the "separation of concerns" principle:
#
#     BAD:  In dashboard/app.py → conn.execute("SELECT COUNT(*) FROM stg_ai_news")
#     GOOD: In analytics/queries.py → def get_total_article_count(engine)
#           In dashboard/app.py    → count = get_total_article_count(engine)
#
#   Benefits of this separation:
#     1. Dashboard code stays readable (no SQL strings cluttering it)
#     2. Queries can be unit-tested independently of the UI
#     3. Multiple pages can call the same query function (no duplication)
#     4. Changing a query only requires one file change, not hunting through UI code
#
# WEEK 2:
#   This package is used by the Streamlit dashboard (Module 3+).
#   It queries the stg_ai_news staging table — NEVER the raw layer.
#
# =============================================================================
