# =============================================================================
# dashboard/__init__.py — AI Pulse Dashboard
# =============================================================================
#
# PURPOSE:
#   Makes 'dashboard' a Python package.
#
# DASHBOARD STRUCTURE:
#   dashboard/
#     __init__.py          <- This file
#     app.py               <- Home page (run with: streamlit run dashboard/app.py)
#     components/
#       styles.py          <- CSS injection (applied to every page)
#       kpi_cards.py       <- 4 header KPI metric cards
#       charts.py          <- Plotly chart factory functions
#       article_card.py    <- Reusable article display component
#       sidebar.py         <- Left sidebar (nav + pipeline health)
#     utils/
#       db_helper.py       <- Cached DB engine (created once, shared across pages)
#       formatters.py      <- Number, date, score formatting helpers
#
# HOW TO RUN:
#   streamlit run dashboard/app.py
#
# =============================================================================
