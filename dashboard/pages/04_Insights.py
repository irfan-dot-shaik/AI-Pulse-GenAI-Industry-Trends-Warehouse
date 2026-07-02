# =============================================================================
# dashboard/pages/04_Insights.py — Placeholder (built in Module 6)
# =============================================================================
import sys, os
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

import streamlit as st
st.set_page_config(page_title="Insights — AI Pulse", page_icon="💡", layout="wide")

from dashboard.components.styles import inject_styles, render_page_header
from dashboard.components.sidebar import render_sidebar
from dashboard.utils.db_helper import get_engine

inject_styles()
engine = get_engine()
render_sidebar(engine, current_page="Insights")

render_page_header("AI Insights", "Keyword trends, company mentions and topic analysis — built in Module 6.", icon="💡")
st.info("🚧 **Coming in Module 6.** Keyword frequency, company mention charts, and AI trend narrative.", icon="💡")
