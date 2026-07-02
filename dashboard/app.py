# =============================================================================
# dashboard/app.py — AI Pulse Dashboard: Home Page
# =============================================================================
#
# DESIGN LANGUAGE: Old Money · Quiet Luxury · Executive Dashboard
#
# Home page sections:
#   1. KPI Cards         — Total, Today, Sources, Avg Score
#   2. Top Intelligence  — Top 7 scored articles + score donut
#   3. Trend Analytics   — Articles per day + source bar
#   4. Recent Articles   — Latest 5 ingested
#   5. Pipeline Guide    — How it works (for mentor demo)
#
# RUN:
#   streamlit run dashboard/app.py
#
# =============================================================================

import sys
import os

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

import streamlit as st

st.set_page_config(
    page_title="AI Pulse — GenAI Industry Intelligence",
    page_icon="◆",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get Help": None,
        "Report a bug": None,
        "About": (
            "**AI Pulse** — GenAI Industry Trends Warehouse\n\n"
            "Built by Shaik Irfan · B.Tech CSE-AIDE\n"
            "Foundations of Data Engineering · Week 2"
        ),
    },
)

from dashboard.utils.db_helper import get_engine, is_db_connected
from dashboard.components.styles import inject_styles, render_page_header, render_section_header
from dashboard.components.kpi_cards import render_kpi_cards
from dashboard.components.sidebar import render_sidebar
from dashboard.components.charts import (
    make_articles_per_day_line,
    make_category_donut,
    make_source_bar,
)
from dashboard.components.article_card import render_compact_article_row
from analytics.queries import (
    get_top_scored_articles,
    get_articles_per_day,
    get_score_category_distribution,
    get_articles_per_source,
    get_latest_articles,
)
from dashboard.utils.formatters import format_relative_time

# ── Inject Design System ──────────────────────────────────────────────────────
inject_styles()

# ── Database ──────────────────────────────────────────────────────────────────
engine = get_engine()

# ── Sidebar ───────────────────────────────────────────────────────────────────
render_sidebar(engine, current_page="Home")

# ── Connection Guard ──────────────────────────────────────────────────────────
if not is_db_connected(engine):
    st.markdown(
        """
        <div style="max-width:520px; margin:4rem auto; text-align:center;
                    font-family:'Inter',sans-serif;">
            <div style="font-size:2.5rem; margin-bottom:1rem; opacity:0.3;">◆</div>
            <div style="font-family:'Cormorant Garamond',serif; font-size:1.8rem;
                        font-weight:600; color:#F7F5F2; margin-bottom:0.6rem;">
                Database Offline
            </div>
            <div style="color:#A9B1A6; font-size:0.88rem; line-height:1.7;
                        margin-bottom:1.5rem;">
                PostgreSQL is not reachable. Start the database, then run the pipeline
                to populate your warehouse.
            </div>
            <code style="background:#1C2721; color:#C8A96A; padding:0.8rem 1.2rem;
                         border-radius:8px; font-size:0.82rem; display:block;
                         border:1px solid rgba(200,169,106,0.15); text-align:left;">
                # 1. Start PostgreSQL<br>
                # 2. python main.py<br>
                # 3. streamlit run dashboard/app.py
            </code>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.stop()

# ── Page Header ───────────────────────────────────────────────────────────────
render_page_header(
    title="GenAI Industry Intelligence",
    subtitle=(
        "Real-time AI news analysis across OpenAI, Anthropic, Google, NVIDIA and "
        "leading publishers — validated, scored, and ready for analysis."
    ),
)

# ── Section 1: KPI Cards ──────────────────────────────────────────────────────
render_section_header("Key Metrics")
render_kpi_cards(engine)

# ── Section 2: Top Intelligence + Score Mix ───────────────────────────────────
render_section_header("Intelligence Briefing")

col_articles, col_donut = st.columns([3, 2], gap="large")

with col_articles:
    st.markdown(
        "<div style='font-family:Inter,sans-serif;font-size:0.68rem;font-weight:700;"
        "letter-spacing:0.12em;text-transform:uppercase;color:#6B7566;"
        "margin-bottom:1rem;'>Highest Scored Articles</div>",
        unsafe_allow_html=True,
    )
    top_df = get_top_scored_articles(engine, limit=7)
    if top_df.empty:
        st.markdown(
            '<div class="empty-state"><span class="empty-state-icon">◇</span>'
            '<div class="empty-state-title">No Articles Yet</div>'
            '<div class="empty-state-sub">Run <code>python main.py</code> to ingest data.</div></div>',
            unsafe_allow_html=True,
        )
    else:
        for rank, (_, row) in enumerate(top_df.iterrows(), start=1):
            render_compact_article_row(row, rank=rank)

with col_donut:
    st.markdown(
        "<div style='font-family:Inter,sans-serif;font-size:0.68rem;font-weight:700;"
        "letter-spacing:0.12em;text-transform:uppercase;color:#6B7566;"
        "margin-bottom:1rem;'>Score Distribution</div>",
        unsafe_allow_html=True,
    )
    cat_df = get_score_category_distribution(engine)
    fig_donut = make_category_donut(cat_df)
    st.plotly_chart(fig_donut, width="stretch", config={"displayModeBar": False})

    # Legend
    st.markdown(
        """
        <div style="font-size:0.74rem; color:#6B7566; line-height:2.1;
                    padding:0.4rem 0.2rem; border-top:1px solid rgba(200,169,106,0.08);
                    margin-top:0.2rem;">
            <span style="color:#C8A96A;">—</span> <b style="color:#A9B1A6;">Gold</b> &nbsp;Hot Trend · 90–100
            &nbsp;&nbsp;
            <span style="color:#C9984A;">—</span> <b style="color:#A9B1A6;">Amber</b> &nbsp;High Impact · 75–89<br>
            <span style="color:#6E9F67;">—</span> <b style="color:#A9B1A6;">Green</b> &nbsp;Trending · 50–74
            &nbsp;&nbsp;
            <span style="color:#7A8078;">—</span> <b style="color:#A9B1A6;">Stone</b> &nbsp;Normal · 0–49
        </div>
        """,
        unsafe_allow_html=True,
    )

# ── Section 3: Charts ─────────────────────────────────────────────────────────
render_section_header("Trend Analytics")

col_trend, col_sources = st.columns(2, gap="large")

with col_trend:
    trend_df = get_articles_per_day(engine, days=30)
    st.plotly_chart(
        make_articles_per_day_line(trend_df),
        width="stretch",
        config={"displayModeBar": False},
    )

with col_sources:
    source_df = get_articles_per_source(engine, top_n=8)
    st.plotly_chart(
        make_source_bar(source_df),
        width="stretch",
        config={"displayModeBar": False},
    )

# ── Section 4: Recent Articles ────────────────────────────────────────────────
render_section_header("Recently Ingested")

latest_df = get_latest_articles(engine, limit=5)

if latest_df.empty:
    st.markdown(
        '<div class="empty-state"><span class="empty-state-icon">◇</span>'
        '<div class="empty-state-title">No Recent Articles</div>'
        '<div class="empty-state-sub">Run the pipeline to ingest data.</div></div>',
        unsafe_allow_html=True,
    )
else:
    for _, row in latest_df.iterrows():
        title    = str(row.get("title", "Untitled"))
        source   = str(row.get("source", "Unknown"))
        url      = str(row.get("url", "#"))
        score    = int(row.get("intelligence_score", 0))
        category = str(row.get("score_category", "Normal"))
        relative = format_relative_time(row.get("published_at"))
        badge_cls = {
            "Hot Trend": "badge-hot", "High Impact": "badge-high",
            "Trending": "badge-trend", "Normal": "badge-normal",
        }.get(category, "badge-normal")

        st.markdown(
            f"""
            <div class="article-card" style="padding:0.85rem 1.4rem;">
                <div style="display:flex; justify-content:space-between; align-items:center; gap:1rem;">
                    <a href="{url}" target="_blank" rel="noopener"
                       style="font-family:'Inter',sans-serif;font-size:0.9rem;font-weight:600;
                              color:#F7F5F2;text-decoration:none;flex:1;min-width:0;
                              overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">
                        {title}
                    </a>
                    <span class="badge {badge_cls}" style="flex-shrink:0;">{score}</span>
                </div>
                <div style="font-size:0.74rem;color:#6B7566;margin-top:0.3rem;">
                    {source} · {relative}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

# ── Section 5: Pipeline Guide ─────────────────────────────────────────────────
render_section_header("How It Works")

st.markdown(
    """
    <div style="display:grid; grid-template-columns:1fr 1fr 1fr; gap:1.2rem;">
        <div style="background:#1C2721; border:1px solid rgba(200,169,106,0.08);
                    border-radius:12px; padding:1.4rem 1.5rem;">
            <div style="font-family:'Inter',sans-serif; font-size:0.65rem; font-weight:700;
                        letter-spacing:0.12em; text-transform:uppercase;
                        color:#C8A96A; margin-bottom:0.6rem;">01 · Ingest</div>
            <div style="font-family:'Inter',sans-serif; font-size:0.84rem;
                        color:#A9B1A6; line-height:1.7;">
                <code style="color:#C8A96A;">python main.py</code> fetches AI news
                from GNews API. Each article lands in
                <code style="color:#C8A96A;">raw_ai_news</code> — an immutable audit trail
                that is never modified.
            </div>
        </div>
        <div style="background:#1C2721; border:1px solid rgba(200,169,106,0.08);
                    border-radius:12px; padding:1.4rem 1.5rem;">
            <div style="font-family:'Inter',sans-serif; font-size:0.65rem; font-weight:700;
                        letter-spacing:0.12em; text-transform:uppercase;
                        color:#6E9F67; margin-bottom:0.6rem;">02 · Process</div>
            <div style="font-family:'Inter',sans-serif; font-size:0.84rem;
                        color:#A9B1A6; line-height:1.7;">
                The pipeline validates (5 rules), normalises text, and scores each
                article 0–100 using four transparent criteria. Clean records populate
                <code style="color:#6E9F67;">stg_ai_news</code>.
            </div>
        </div>
        <div style="background:#1C2721; border:1px solid rgba(200,169,106,0.08);
                    border-radius:12px; padding:1.4rem 1.5rem;">
            <div style="font-family:'Inter',sans-serif; font-size:0.65rem; font-weight:700;
                        letter-spacing:0.12em; text-transform:uppercase;
                        color:#A9B1A6; margin-bottom:0.6rem;">03 · Analyse</div>
            <div style="font-family:'Inter',sans-serif; font-size:0.84rem;
                        color:#A9B1A6; line-height:1.7;">
                This dashboard reads exclusively from
                <code style="color:#A9B1A6;">stg_ai_news</code>.
                Navigate to Explorer, Analytics, Top AI News, and Insights
                via the sidebar.
            </div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown("<div style='height:3rem;'></div>", unsafe_allow_html=True)
