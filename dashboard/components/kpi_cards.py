# =============================================================================
# dashboard/components/kpi_cards.py — AI Pulse Dashboard
# =============================================================================
#
# DESIGN: Premium KPI metric cards for the home page.
# Uses st.metric() styled via CSS (the card styles are in styles.py).
# Four cards in a horizontal row: Total, Today, Sources, Avg Score.
#
# =============================================================================

import streamlit as st
from sqlalchemy.engine import Engine

from analytics.queries import (
    get_total_article_count,
    get_todays_article_count,
    get_unique_source_count,
    get_average_intelligence_score,
)
from dashboard.utils.formatters import format_number, format_score


def render_kpi_cards(engine: Engine) -> None:
    """
    Render four KPI metric cards in a horizontal 4-column layout.

    Each card is styled via the metric-container CSS rules in styles.py.
    Queries all four values from stg_ai_news via analytics functions.

    Args:
        engine: Connected SQLAlchemy engine from db_helper.get_engine().
    """
    total   = get_total_article_count(engine)
    today   = get_todays_article_count(engine)
    sources = get_unique_source_count(engine)
    avg     = get_average_intelligence_score(engine)

    c1, c2, c3, c4 = st.columns(4, gap="medium")

    with c1:
        st.metric(
            label="Total Articles",
            value=format_number(total),
            delta="Staging layer",
            help="Total validated and scored articles in stg_ai_news.",
        )

    with c2:
        st.metric(
            label="Published Today",
            value=format_number(today),
            delta="UTC date",
            help="Articles with published_at = today (UTC).",
        )

    with c3:
        st.metric(
            label="Unique Sources",
            value=format_number(sources),
            delta="Publishers",
            help="Count of distinct news publishers in the staging table.",
        )

    with c4:
        st.metric(
            label="Avg. Intelligence",
            value=format_score(avg),
            delta="Scored 0–100",
            help=(
                "Average AI Intelligence Score across all staged articles. "
                "Measures recency, keyword density, source credibility, and length."
            ),
        )
