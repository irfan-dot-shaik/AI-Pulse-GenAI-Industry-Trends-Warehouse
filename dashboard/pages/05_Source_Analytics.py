# =============================================================================
# dashboard/pages/05_Source_Analytics.py — AI Pulse Dashboard
# =============================================================================
# MODULE 8: Source Analytics — Week 3 Multi-Source Intelligence
#
# This page provides a dedicated view of data quality and intelligence
# across all ingestion sources: GNews, Hacker News, and Reddit.
#
# Sections:
#   1. Executive Summary Cards   — 4 high-level KPIs
#   2. Source Contribution       — donut chart + horizontal bar
#   3. Intelligence Score By Source — grouped bar comparison
#   4. Publication Trends By Source — multi-line trend chart
#   5. Top Keywords By Source    — faceted bar chart per source
#   6. Source Ranking Table      — detailed tabular breakdown
# =============================================================================

import sys
import os

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

import streamlit as st

st.set_page_config(
    page_title="Source Analytics — AI Pulse",
    page_icon="◆",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Imports ────────────────────────────────────────────────────────────────────
from dashboard.utils.db_helper import get_engine, is_db_connected
from dashboard.components.styles import inject_styles, render_page_header, render_section_header
from dashboard.components.sidebar import render_sidebar
from dashboard.components.footer import render_footer
from dashboard.utils.formatters import format_number, format_score
from dashboard.utils.cached_queries import (
    cached_source_breakdown,
    cached_keywords_by_source,
    cached_daily_trend_by_source,
    cached_total_articles,
    cached_unique_sources,
    cached_avg_score,
)

import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

# ── Design tokens (matching existing dashboard palette) ─────────────────────
_GOLD       = "#C8A96A"
_GOLD_LIGHT = "#D8C18B"
_BG_CARD    = "#19221D"
_TEXT       = "#F7F5F2"
_MUTED      = "#A9B1A6"
_SUCCESS    = "#6E9F67"
_WARNING    = "#C9984A"

# Source colour palette — consistent across all charts on this page
_SOURCE_COLORS = {
    "GNews":         "#C8A96A",   # Antique gold — primary source
    "Hacker News":   "#6E9F67",   # Forest green
    "Reddit/MachineLearning": "#7B9EBD",  # Muted blue
    "Reddit/artificial":      "#9B7EBD",  # Muted violet
    "Reddit/singularity":     "#BD8E7E",  # Muted terracotta
}
_DEFAULT_COLOR = "#8A9A85"  # Fallback for unknown sources

PLOTLY_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter, sans-serif", color=_TEXT, size=12),
    margin=dict(l=0, r=0, t=30, b=0),
    showlegend=True,
    legend=dict(
        bgcolor="rgba(0,0,0,0)",
        font=dict(color=_TEXT, size=11),
    ),
)


def _get_source_color(source: str) -> str:
    """Return a consistent colour for a source name."""
    return _SOURCE_COLORS.get(source, _DEFAULT_COLOR)


def _source_color_list(sources: list[str]) -> list[str]:
    """Return a list of colours matching the given source names."""
    return [_get_source_color(s) for s in sources]


# =============================================================================
# Page Setup
# =============================================================================

inject_styles()
engine = get_engine()
render_sidebar(engine, current_page="Source Analytics")
render_page_header(
    title="Source Analytics",
    subtitle="Multi-source intelligence — GNews · Hacker News · Reddit",
)

# =============================================================================
# DB Connection Guard
# =============================================================================

if not is_db_connected(engine):
    st.error(
        "⚠️ Database connection unavailable. "
        "Source Analytics requires PostgreSQL to be running."
    )
    st.stop()

# =============================================================================
# Data Load
# =============================================================================

with st.spinner("Loading source analytics..."):
    source_df        = cached_source_breakdown(engine)
    keywords_df      = cached_keywords_by_source(engine)
    daily_source_df  = cached_daily_trend_by_source(engine)
    total_articles   = cached_total_articles(engine)
    unique_sources   = cached_unique_sources(engine)
    avg_score_global = cached_avg_score(engine)

# Empty state guard
if source_df is None or source_df.empty:
    st.info(
        "📭 No multi-source data available yet.\n\n"
        "Run `python main.py` to ingest articles from GNews, Hacker News, and Reddit."
    )
    render_footer()
    st.stop()

# =============================================================================
# SECTION 1 — Executive Summary
# =============================================================================

render_section_header("Executive Summary")

n_sources = len(source_df)
top_source = source_df.iloc[0]["source"] if not source_df.empty else "—"
top_source_count = int(source_df.iloc[0]["article_count"]) if not source_df.empty else 0
best_avg_row = source_df.loc[source_df["avg_score"].idxmax()] if not source_df.empty else None
best_avg_source = best_avg_row["source"] if best_avg_row is not None else "—"
best_avg_score = float(best_avg_row["avg_score"]) if best_avg_row is not None else 0.0

col1, col2, col3, col4 = st.columns(4)

_card_css = """
    background: #19221D;
    border: 1px solid rgba(200,169,106,0.12);
    border-radius: 10px;
    padding: 1.2rem 1.4rem;
    text-align: center;
"""

with col1:
    st.markdown(
        f"""<div style="{_card_css}">
            <div style="font-size:0.72rem;color:#A9B1A6;text-transform:uppercase;
                        letter-spacing:0.1em;margin-bottom:0.4rem;">Active Sources</div>
            <div style="font-size:2rem;font-weight:700;color:#C8A96A;
                        font-family:'Space Grotesk',sans-serif;">{n_sources}</div>
            <div style="font-size:0.72rem;color:#A9B1A6;margin-top:0.25rem;">
                pipelines running
            </div>
        </div>""",
        unsafe_allow_html=True,
    )

with col2:
    st.markdown(
        f"""<div style="{_card_css}">
            <div style="font-size:0.72rem;color:#A9B1A6;text-transform:uppercase;
                        letter-spacing:0.1em;margin-bottom:0.4rem;">Total Articles</div>
            <div style="font-size:2rem;font-weight:700;color:#C8A96A;
                        font-family:'Space Grotesk',sans-serif;">{format_number(total_articles)}</div>
            <div style="font-size:0.72rem;color:#A9B1A6;margin-top:0.25rem;">
                in staging layer
            </div>
        </div>""",
        unsafe_allow_html=True,
    )

with col3:
    st.markdown(
        f"""<div style="{_card_css}">
            <div style="font-size:0.72rem;color:#A9B1A6;text-transform:uppercase;
                        letter-spacing:0.1em;margin-bottom:0.4rem;">Top Source</div>
            <div style="font-size:1.5rem;font-weight:700;color:#C8A96A;
                        font-family:'Space Grotesk',sans-serif;">{top_source}</div>
            <div style="font-size:0.72rem;color:#A9B1A6;margin-top:0.25rem;">
                {format_number(top_source_count)} articles
            </div>
        </div>""",
        unsafe_allow_html=True,
    )

with col4:
    st.markdown(
        f"""<div style="{_card_css}">
            <div style="font-size:0.72rem;color:#A9B1A6;text-transform:uppercase;
                        letter-spacing:0.1em;margin-bottom:0.4rem;">Best Avg Score</div>
            <div style="font-size:2rem;font-weight:700;color:#C8A96A;
                        font-family:'Space Grotesk',sans-serif;">{best_avg_score:.1f}</div>
            <div style="font-size:0.72rem;color:#A9B1A6;margin-top:0.25rem;">
                {best_avg_source}
            </div>
        </div>""",
        unsafe_allow_html=True,
    )

st.markdown("<div style='height:1.5rem'></div>", unsafe_allow_html=True)

# =============================================================================
# SECTION 2 — Source Contribution
# =============================================================================

render_section_header("Source Contribution")

col_donut, col_bar = st.columns([1, 1], gap="large")

with col_donut:
    st.markdown("##### Article Share by Source")
    fig_donut = go.Figure(
        go.Pie(
            labels=source_df["source"].tolist(),
            values=source_df["article_count"].tolist(),
            hole=0.55,
            marker=dict(
                colors=_source_color_list(source_df["source"].tolist()),
                line=dict(color="#0D120F", width=2),
            ),
            textfont=dict(family="Inter, sans-serif", size=12, color=_TEXT),
            hovertemplate="<b>%{label}</b><br>%{value} articles (%{percent})<extra></extra>",
        )
    )
    fig_donut.add_annotation(
        text=f"<b>{format_number(total_articles)}</b><br><span style='font-size:10px'>articles</span>",
        x=0.5, y=0.5,
        font=dict(size=16, color=_GOLD, family="Space Grotesk, sans-serif"),
        showarrow=False,
    )
    fig_donut.update_layout(
        **PLOTLY_LAYOUT,
        height=320,
        legend=dict(orientation="h", yanchor="top", y=-0.1, xanchor="center", x=0.5,
                    font=dict(color=_TEXT, size=11)),
    )
    st.plotly_chart(fig_donut, use_container_width=True)

with col_bar:
    st.markdown("##### Articles per Source")
    fig_hbar = px.bar(
        source_df,
        x="article_count",
        y="source",
        orientation="h",
        color="source",
        color_discrete_map=_SOURCE_COLORS,
        text="article_count",
        hover_data={"pct_of_total": ":.1f", "article_count": True},
        labels={"article_count": "Articles", "source": ""},
    )
    fig_hbar.update_traces(
        textposition="outside",
        textfont=dict(color=_GOLD, size=12, family="Space Grotesk, sans-serif"),
        marker_line_width=0,
    )
    fig_hbar.update_layout(
        **PLOTLY_LAYOUT,
        height=320,
        showlegend=False,
        xaxis=dict(gridcolor="rgba(200,169,106,0.06)", color=_MUTED),
        yaxis=dict(gridcolor="rgba(0,0,0,0)", color=_MUTED),
    )
    st.plotly_chart(fig_hbar, use_container_width=True)

st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)

# =============================================================================
# SECTION 3 — Intelligence Score Comparison
# =============================================================================

render_section_header("Intelligence Score by Source")

col_avg, col_max = st.columns(2, gap="large")

with col_avg:
    st.markdown("##### Average Intelligence Score")
    fig_avg = px.bar(
        source_df.sort_values("avg_score", ascending=True),
        x="avg_score",
        y="source",
        orientation="h",
        color="source",
        color_discrete_map=_SOURCE_COLORS,
        text="avg_score",
        range_x=[0, 100],
        labels={"avg_score": "Avg Score (0–100)", "source": ""},
    )
    fig_avg.add_vline(
        x=avg_score_global,
        line_dash="dot",
        line_color=_GOLD,
        annotation_text=f" Global avg: {avg_score_global:.1f}",
        annotation_font_color=_GOLD,
        annotation_font_size=11,
    )
    fig_avg.update_traces(
        texttemplate="%{text:.1f}",
        textposition="outside",
        textfont=dict(color=_GOLD, size=12, family="Space Grotesk, sans-serif"),
        marker_line_width=0,
    )
    fig_avg.update_layout(
        **PLOTLY_LAYOUT,
        height=300,
        showlegend=False,
        xaxis=dict(gridcolor="rgba(200,169,106,0.06)", color=_MUTED),
        yaxis=dict(color=_MUTED),
    )
    st.plotly_chart(fig_avg, use_container_width=True)

with col_max:
    st.markdown("##### Max Intelligence Score")
    fig_max = px.bar(
        source_df.sort_values("max_score", ascending=True),
        x="max_score",
        y="source",
        orientation="h",
        color="source",
        color_discrete_map=_SOURCE_COLORS,
        text="max_score",
        range_x=[0, 100],
        labels={"max_score": "Max Score (0–100)", "source": ""},
    )
    fig_max.update_traces(
        textposition="outside",
        textfont=dict(color=_GOLD, size=12, family="Space Grotesk, sans-serif"),
        marker_line_width=0,
    )
    fig_max.update_layout(
        **PLOTLY_LAYOUT,
        height=300,
        showlegend=False,
        xaxis=dict(gridcolor="rgba(200,169,106,0.06)", color=_MUTED),
        yaxis=dict(color=_MUTED),
    )
    st.plotly_chart(fig_max, use_container_width=True)

st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)

# =============================================================================
# SECTION 4 — Publication Trends by Source
# =============================================================================

render_section_header("Publication Trends by Source")

if daily_source_df is not None and not daily_source_df.empty:
    daily_source_df["published_date"] = pd.to_datetime(daily_source_df["published_date"])

    fig_trend = px.line(
        daily_source_df,
        x="published_date",
        y="article_count",
        color="source",
        color_discrete_map=_SOURCE_COLORS,
        markers=True,
        labels={
            "published_date": "Publication Date",
            "article_count": "Articles",
            "source": "Source",
        },
        title="",
    )
    fig_trend.update_traces(line_width=2, marker_size=5)
    fig_trend.update_layout(
        **PLOTLY_LAYOUT,
        height=340,
        xaxis=dict(
            gridcolor="rgba(200,169,106,0.06)",
            color=_MUTED,
            title_font=dict(color=_MUTED, size=11),
        ),
        yaxis=dict(
            gridcolor="rgba(200,169,106,0.06)",
            color=_MUTED,
            title_font=dict(color=_MUTED, size=11),
        ),
    )
    st.plotly_chart(fig_trend, use_container_width=True)
else:
    st.info("Trend data requires at least 2 days of ingestion history.")

st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)

# =============================================================================
# SECTION 5 — Top Keywords by Source
# =============================================================================

render_section_header("Top Keywords by Source")

if keywords_df is not None and not keywords_df.empty:
    sources_in_kw = keywords_df["source"].unique().tolist()
    n_sources_kw = len(sources_in_kw)

    # Build one column per source
    cols = st.columns(n_sources_kw, gap="large")

    for col, src in zip(cols, sources_in_kw):
        src_kw = keywords_df[keywords_df["source"] == src].head(8)
        with col:
            st.markdown(f"##### {src}")
            fig_kw = px.bar(
                src_kw.sort_values("count"),
                x="count",
                y="keyword",
                orientation="h",
                color_discrete_sequence=[_get_source_color(src)],
                labels={"count": "Articles", "keyword": ""},
                text="count",
            )
            fig_kw.update_traces(
                textposition="outside",
                textfont=dict(size=11, color=_MUTED),
                marker_line_width=0,
            )
            fig_kw.update_layout(
                **PLOTLY_LAYOUT,
                height=300,
                showlegend=False,
                xaxis=dict(gridcolor="rgba(200,169,106,0.06)", color=_MUTED),
                yaxis=dict(color=_MUTED),
            )
            st.plotly_chart(fig_kw, use_container_width=True)
else:
    st.info(
        "Keyword data is not available. "
        "This populates after articles with AI keywords are processed."
    )

st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)

# =============================================================================
# SECTION 6 — Source Ranking Table
# =============================================================================

render_section_header("Source Ranking Table")

if not source_df.empty:
    display_df = source_df.copy()

    # Format columns for display
    display_df["article_count"] = display_df["article_count"].apply(format_number)
    display_df["avg_score"]     = display_df["avg_score"].apply(lambda x: f"{x:.1f}")
    display_df["max_score"]     = display_df["max_score"].apply(str)
    display_df["pct_of_total"]  = display_df["pct_of_total"].apply(lambda x: f"{x:.1f}%")

    display_df.columns = ["Source", "Articles", "Avg Score", "Max Score", "Share %"]
    display_df.index = range(1, len(display_df) + 1)

    st.dataframe(
        display_df,
        use_container_width=True,
        column_config={
            "Source":    st.column_config.TextColumn("Source", width="medium"),
            "Articles":  st.column_config.TextColumn("Articles", width="small"),
            "Avg Score": st.column_config.TextColumn("Avg Score", width="small"),
            "Max Score": st.column_config.TextColumn("Max Score", width="small"),
            "Share %":   st.column_config.TextColumn("Share %", width="small"),
        },
    )

# =============================================================================
# Footer
# =============================================================================

render_footer()
