# =============================================================================
# dashboard/pages/02_Analytics.py — AI Pulse Dashboard
# =============================================================================
# MODULE 5: Analytics Page
#
# Sections:
#   1. Executive Summary    — 6 KPI cards
#   2. Interactive Charts   — source bar, trend line, donut, keyword bar, histogram
#   3. Publisher Performance — ranked table
#   4. Top 10 Articles      — reuses render_compact_article_row
#   5. Pipeline Health      — status table
# =============================================================================

import sys
import os

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

import streamlit as st

st.set_page_config(
    page_title="Analytics — AI Pulse",
    page_icon="◆",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Imports ───────────────────────────────────────────────────────────────────
from dashboard.utils.db_helper import get_engine, is_db_connected
from dashboard.components.styles import inject_styles, render_page_header, render_section_header
from dashboard.components.sidebar import render_sidebar
from dashboard.components.charts import (
    make_source_bar,
    make_articles_per_day_line,
    make_category_donut,
    make_keyword_bar,
    make_score_histogram,
)
from dashboard.components.article_card import render_compact_article_row
from dashboard.components.footer import render_footer
from dashboard.utils.error_boundary import error_boundary
from dashboard.utils.formatters import format_number, format_score
from analytics.queries import (
    get_last_updated_time,
    get_articles_per_day,
    get_top_scored_articles,
    get_pipeline_health,
    get_publisher_performance,
)
from dashboard.utils.cached_queries import (
    cached_total_articles,
    cached_todays_articles,
    cached_unique_sources,
    cached_avg_score,
    cached_max_score,
    cached_category_distribution,
    cached_sources,
    cached_keyword_freq,
)

# ── Setup ─────────────────────────────────────────────────────────────────────
inject_styles()
engine = get_engine()
render_sidebar(engine, current_page="Analytics")

# ── Connection Guard ──────────────────────────────────────────────────────────
if not is_db_connected(engine):
    st.markdown(
        """
        <div style="max-width:480px;margin:5rem auto;text-align:center;font-family:'Inter',sans-serif;">
            <div style="font-size:2rem;opacity:0.2;margin-bottom:1rem;">◆</div>
            <div style="font-family:'Cormorant Garamond',serif;font-size:1.7rem;
                        font-weight:600;color:#F7F5F2;margin-bottom:0.5rem;">Database Offline</div>
            <div style="color:#A9B1A6;font-size:0.86rem;line-height:1.7;">
                Start PostgreSQL and run
                <code style="color:#C8A96A;">python main.py</code> first.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.stop()

# ── Page Header ───────────────────────────────────────────────────────────────
render_page_header(
    title="Analytics",
    subtitle=(
        "In-depth analysis of your GenAI news warehouse — source performance, "
        "score distributions, keyword intelligence, and pipeline health."
    ),
)

# =============================================================================
# SECTION 1 — Executive Summary (6 KPI cards)
# =============================================================================
render_section_header("Executive Summary")

with error_boundary("Failed to load analytics data. Please check database connectivity."):
    with st.spinner("Computing analytics..."):
        total      = cached_total_articles(engine)
        today      = cached_todays_articles(engine)
        sources    = cached_unique_sources(engine)
        avg_score  = cached_avg_score(engine)
        peak_score = cached_max_score(engine)
        last_run   = get_last_updated_time(engine)

k1, k2, k3, k4, k5, k6 = st.columns(6, gap="medium")

with k1:
    st.metric("Total Articles",     format_number(total),    delta="Staging layer")
with k2:
    st.metric("Published Today",    format_number(today),    delta="UTC")
with k3:
    st.metric("Unique Sources",     format_number(sources),  delta="Publishers")
with k4:
    st.metric("Avg. Intelligence",  format_score(avg_score), delta="Mean score")
with k5:
    st.metric("Peak Score",         f"{peak_score} / 100",   delta="Highest article")
with k6:
    st.metric("Last Pipeline Run",  last_run,                delta="UTC timestamp")

# =============================================================================
# SECTION 2 — Interactive Charts
# =============================================================================
render_section_header("Interactive Analytics")

# Row 1: Source bar + Trend line
c_src, c_trend = st.columns(2, gap="large")
with c_src:
    df_src = cached_sources(engine, top_n=10)
    st.plotly_chart(make_source_bar(df_src), width="stretch",
                    config={"displayModeBar": False})

with c_trend:
    df_trend = get_articles_per_day(engine, days=30)
    st.plotly_chart(make_articles_per_day_line(df_trend), width="stretch",
                    config={"displayModeBar": False})

# Row 2: Category donut + Keyword bar + Score histogram
c_donut, c_kw, c_hist = st.columns(3, gap="large")

with c_donut:
    df_cat = cached_category_distribution(engine)
    st.plotly_chart(make_category_donut(df_cat), width="stretch",
                    config={"displayModeBar": False})
    # Legend
    st.markdown(
        """<div style="font-size:0.72rem;color:#6B7566;line-height:2;text-align:center;">
        <span style="color:#C8A96A;">■</span> Gold &nbsp;
        <span style="color:#C9984A;">■</span> Amber &nbsp;
        <span style="color:#6E9F67;">■</span> Green &nbsp;
        <span style="color:#7A8078;">■</span> Stone</div>""",
        unsafe_allow_html=True,
    )

with c_kw:
    df_kw = cached_keyword_freq(engine, top_n=12)
    st.plotly_chart(make_keyword_bar(df_kw), width="stretch",
                    config={"displayModeBar": False})

with c_hist:
    # Histogram needs article-level score data — use top 200 articles
    df_all = get_top_scored_articles(engine, limit=200)
    st.plotly_chart(make_score_histogram(df_all), width="stretch",
                    config={"displayModeBar": False})

# =============================================================================
# SECTION 3 — Publisher Performance
# =============================================================================
render_section_header("Publisher Performance")

df_pub = get_publisher_performance(engine)

if df_pub.empty:
    st.markdown(
        '<div class="empty-state"><span class="empty-state-icon">◇</span>'
        '<div class="empty-state-title">No Publisher Data</div></div>',
        unsafe_allow_html=True,
    )
else:
    # Styled table header
    st.markdown(
        """
        <div style="display:grid;grid-template-columns:2fr 1fr 1fr 1fr 1fr;
                    gap:0.5rem;padding:0.55rem 1rem;
                    background:#1C2721;border-radius:8px 8px 0 0;
                    border:1px solid rgba(200,169,106,0.10);
                    font-family:'Inter',sans-serif;font-size:0.65rem;
                    font-weight:700;letter-spacing:0.10em;text-transform:uppercase;
                    color:#6B7566;margin-bottom:1px;">
            <span>Publisher</span>
            <span style="text-align:right;">Articles</span>
            <span style="text-align:right;">Avg Score</span>
            <span style="text-align:right;">Peak Score</span>
            <span style="text-align:right;">Min Score</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    for i, (_, row) in enumerate(df_pub.iterrows()):
        source       = str(row.get("source", "Unknown"))
        art_count    = int(row.get("article_count", 0))
        avg_s        = float(row.get("avg_score", 0))
        max_s        = int(row.get("max_score", 0))
        min_s        = int(row.get("min_score", 0))
        rank_badge   = f"#{i + 1}"
        row_bg       = "#1C2721" if i % 2 == 0 else "#192118"

        # Colour the avg score based on tier
        if avg_s >= 75:
            score_color = "#C8A96A"
        elif avg_s >= 50:
            score_color = "#6E9F67"
        else:
            score_color = "#7A8078"

        st.markdown(
            f"""
            <div style="display:grid;grid-template-columns:2fr 1fr 1fr 1fr 1fr;
                        gap:0.5rem;padding:0.65rem 1rem;
                        background:{row_bg};
                        border:1px solid rgba(200,169,106,0.06);
                        border-top:none;font-family:'Inter',sans-serif;
                        font-size:0.84rem;color:#A9B1A6;
                        transition:background 180ms ease;">
                <span>
                    <span style="font-family:'Space Grotesk',sans-serif;
                                 font-size:0.68rem;color:#6B7566;margin-right:0.4rem;">
                        {rank_badge}
                    </span>
                    <span style="color:#F7F5F2;font-weight:500;">{source}</span>
                </span>
                <span style="text-align:right;font-family:'Space Grotesk',sans-serif;
                             color:#F7F5F2;font-weight:600;">{art_count}</span>
                <span style="text-align:right;font-family:'Space Grotesk',sans-serif;
                             color:{score_color};font-weight:600;">{avg_s:.1f}</span>
                <span style="text-align:right;font-family:'Space Grotesk',sans-serif;
                             color:#C8A96A;font-weight:600;">{max_s}</span>
                <span style="text-align:right;font-family:'Space Grotesk',sans-serif;
                             color:#6B7566;">{min_s}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

# =============================================================================
# SECTION 4 — Top 10 Articles by Intelligence Score
# =============================================================================
render_section_header("Highest Intelligence Articles")

df_top = get_top_scored_articles(engine, limit=10)

if df_top.empty:
    st.markdown(
        '<div class="empty-state"><span class="empty-state-icon">◇</span>'
        '<div class="empty-state-title">No Articles Yet</div>'
        '<div class="empty-state-sub">Run python main.py to ingest data.</div></div>',
        unsafe_allow_html=True,
    )
else:
    col_a, col_b = st.columns(2, gap="large")
    rows = list(df_top.iterrows())

    for i, (_, row) in enumerate(rows[:5]):
        with col_a:
            render_compact_article_row(row, rank=i + 1)

    for i, (_, row) in enumerate(rows[5:]):
        with col_b:
            render_compact_article_row(row, rank=i + 6)

# =============================================================================
# SECTION 5 — Pipeline Health
# =============================================================================
render_section_header("Pipeline Health")

health = get_pipeline_health(engine)

h1, h2, h3, h4, h5 = st.columns(5, gap="medium")

db_color  = "#6E9F67" if health["db_connected"] else "#B35C4A"
db_label  = "Connected" if health["db_connected"] else "Offline"

with h1:
    st.metric("Database",         db_label,                          delta="PostgreSQL")
with h2:
    st.metric("Raw Layer",        format_number(health["raw_count"]), delta="raw_ai_news")
with h3:
    st.metric("Staging Layer",    format_number(health["staging_count"]), delta="stg_ai_news")
with h4:
    st.metric("Avg. Score",       f"{health['avg_score']:.1f} / 100", delta="All articles")
with h5:
    st.metric("Last Run",         health["last_run"],                 delta="UTC")

# Visual delta note on raw vs staging
if health["raw_count"] > 0 and health["staging_count"] < health["raw_count"]:
    delta_n = health["raw_count"] - health["staging_count"]
    st.markdown(
        f"""
        <div style="margin-top:0.8rem;padding:0.75rem 1.1rem;
                    background:#1C2721;border:1px solid rgba(200,169,106,0.08);
                    border-radius:8px;font-family:'Inter',sans-serif;
                    font-size:0.82rem;color:#A9B1A6;">
            <span style="color:#C9984A;font-weight:600;">{delta_n} article(s)</span>
            in raw_ai_news did not pass validation and were excluded from the staging layer.
            This is expected — the validator enforces 5 data quality rules.
        </div>
        """,
        unsafe_allow_html=True,
    )


render_footer()
