# =============================================================================
# dashboard/components/charts.py — AI Pulse Dashboard
# =============================================================================
#
# DESIGN: Old Money / Quiet Luxury palette.
# All charts use the warm forest-green + antique gold color system.
# No neon. No bright blue. No cyberpunk.
#
# Colors:
#   Gold:    #C8A96A, #D8C18B, #B8935A
#   Green:   #6E9F67, #8BBD85, #4D7548
#   Stone:   #A9B1A6, #7A8078, #5C6359
#   Amber:   #C9984A, #B07D35
#   Terra:   #B35C4A, #9A4A3A
#
# Chart backgrounds match the app surface: #1C2721 paper, #0F1512 plot area.
#
# =============================================================================

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.graph_objects import Figure

# ─────────────────────────────────────────────────────────────────────────────
# Theme Constants
# ─────────────────────────────────────────────────────────────────────────────
_BG       = "#0D120F"
_PAPER    = "#19221D"
_GRID     = "rgba(200,169,106,0.06)"
_TEXT     = "#F7F5F2"
_MUTED    = "#A9B1A6"
_BORDER   = "rgba(200,169,106,0.12)"

# Warm gold palette for sequential/ordinal data
_GOLD_SCALE = [
    [0.0, "#1C2721"],
    [0.3, "#4D3E1A"],
    [0.6, "#9A7030"],
    [1.0, "#C8A96A"],
]

# Categorical palette — warm, muted, never neon
_CAT_PALETTE = ["#C8A96A", "#6E9F67", "#C9984A", "#A9B1A6", "#B35C4A",
                "#D8C18B", "#8BBD85", "#B07D35", "#7A8078", "#9A4A3A"]

# Score category colors — muted and intentional
_CAT_COLORS = {
    "Hot Trend":   "#C8A96A",   # Gold
    "High Impact": "#C9984A",   # Amber
    "Trending":    "#6E9F67",   # Forest green
    "Normal":      "#7A8078",   # Stone
}

# Shared layout applied to every chart
_LAYOUT = dict(
    template="plotly_dark",
    paper_bgcolor=_PAPER,
    plot_bgcolor=_BG,
    font=dict(family="'Space Grotesk', 'Inter', sans-serif", color=_MUTED, size=12),
    margin=dict(l=16, r=16, t=44, b=16),
    legend=dict(
        bgcolor="rgba(28,39,33,0.8)",
        bordercolor=_BORDER,
        borderwidth=1,
        font=dict(size=11, color=_MUTED),
    ),
    hoverlabel=dict(
        bgcolor="#21302A",
        bordercolor="rgba(200,169,106,0.3)",
        font=dict(family="Inter", size=12, color=_TEXT),
    ),
    xaxis=dict(
        gridcolor=_GRID,
        linecolor=_GRID,
        zerolinecolor=_GRID,
        tickfont=dict(color=_MUTED, size=11),
    ),
    yaxis=dict(
        gridcolor=_GRID,
        linecolor=_GRID,
        zerolinecolor=_GRID,
        tickfont=dict(color=_MUTED, size=11),
    ),
)


def _theme(fig: Figure, title: str = "") -> Figure:
    """Apply shared theme and optional title to any Plotly figure."""
    fig.update_layout(**_LAYOUT)
    if title:
        fig.update_layout(title=dict(
            text=title,
            font=dict(size=13, color=_MUTED, family="Inter"),
            x=0.0, xanchor="left",
            pad=dict(l=4),
        ))
    return fig


def _empty(message: str = "No data") -> Figure:
    """Graceful empty-state figure when a query returns no rows."""
    fig = go.Figure()
    fig.add_annotation(
        text=message, x=0.5, y=0.5,
        xref="paper", yref="paper", showarrow=False,
        font=dict(size=14, color=_MUTED, family="Inter"),
    )
    fig.update_layout(
        paper_bgcolor=_PAPER, plot_bgcolor=_BG, height=240,
        xaxis=dict(visible=False), yaxis=dict(visible=False),
    )
    return fig


# =============================================================================
# Source Bar — horizontal bar by article count
# =============================================================================
def make_source_bar(df: pd.DataFrame) -> Figure:
    """
    Horizontal bar chart: article count grouped by news source.
    Used on Home and Analytics pages.
    """
    if df is None or df.empty:
        return _empty("No source data")

    df_s = df.sort_values("article_count", ascending=True).tail(10)

    fig = go.Figure(go.Bar(
        x=df_s["article_count"],
        y=df_s["source"],
        orientation="h",
        marker=dict(
            color=df_s["article_count"],
            colorscale=_GOLD_SCALE,
            showscale=False,
            line=dict(color="rgba(0,0,0,0)", width=0),
        ),
        text=df_s["article_count"],
        textposition="outside",
        textfont=dict(color=_MUTED, size=11),
        hovertemplate="<b>%{y}</b><br>Articles: <b>%{x}</b><extra></extra>",
    ))

    return _theme(fig, "Articles by Source")


# =============================================================================
# Articles Per Day — area line chart
# =============================================================================
def make_articles_per_day_line(df: pd.DataFrame) -> Figure:
    """
    Area line chart showing daily article publication volume.
    Gold line with subtle fill.
    """
    if df is None or df.empty:
        return _empty("No time-series data")

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["publish_date"],
        y=df["article_count"],
        mode="lines",
        fill="tozeroy",
        line=dict(color="#C8A96A", width=2),
        fillcolor="rgba(200,169,106,0.08)",
        hovertemplate="<b>%{x|%b %d}</b><br>Articles: <b>%{y}</b><extra></extra>",
    ))

    fig.update_xaxes(tickformat="%b %d", tickangle=-25)
    return _theme(fig, "Publications Per Day")


# =============================================================================
# Ingestion Trend — compact sparkline style
# =============================================================================
def make_ingestion_trend(df: pd.DataFrame) -> Figure:
    """
    Compact area line for daily ingestion trend (pipeline activity).
    """
    if df is None or df.empty:
        return _empty("No ingestion data")

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["process_date"],
        y=df["article_count"],
        mode="lines+markers",
        fill="tozeroy",
        line=dict(color="#6E9F67", width=2),
        fillcolor="rgba(110,159,103,0.08)",
        marker=dict(size=5, color="#6E9F67"),
        hovertemplate="<b>%{x|%b %d}</b><br>Processed: <b>%{y}</b><extra></extra>",
    ))

    fig.update_xaxes(tickformat="%b %d", tickangle=-25)
    return _theme(fig, "Daily Pipeline Activity")


# =============================================================================
# Category Donut
# =============================================================================
def make_category_donut(df: pd.DataFrame) -> Figure:
    """
    Donut chart: distribution of Hot Trend / High Impact / Trending / Normal.
    Uses the warm muted palette — no bright colours.
    """
    if df is None or df.empty:
        return _empty("No category data")

    colors = [_CAT_COLORS.get(c, "#7A8078") for c in df["score_category"]]

    fig = go.Figure(go.Pie(
        labels=df["score_category"],
        values=df["article_count"],
        hole=0.62,
        marker=dict(colors=colors, line=dict(color=_BG, width=3)),
        textinfo="label+percent",
        textfont=dict(size=11, family="Inter", color=_TEXT),
        hovertemplate="<b>%{label}</b><br>%{value} articles · %{percent}<extra></extra>",
    ))

    fig.update_layout(
        showlegend=False,
        annotations=[dict(
            text="Score<br>Mix",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=12, color=_MUTED, family="Inter"),
        )],
        height=280,
    )

    return _theme(fig)


# =============================================================================
# Keyword Frequency Bar
# =============================================================================
def make_keyword_bar(df: pd.DataFrame) -> Figure:
    """
    Horizontal bar of most-mentioned AI keywords.
    Opacity scales with frequency — more mentions = more opaque gold.
    """
    if df is None or df.empty:
        return _empty("No keyword data")

    df_s = df.sort_values("frequency", ascending=True)
    max_f = df_s["frequency"].max() or 1

    colors = [
        f"rgba(200,169,106,{0.25 + 0.6 * v / max_f:.2f})"
        for v in df_s["frequency"]
    ]

    fig = go.Figure(go.Bar(
        x=df_s["frequency"], y=df_s["keyword"],
        orientation="h",
        marker=dict(color=colors, line=dict(width=0)),
        text=df_s["frequency"],
        textposition="outside",
        textfont=dict(color=_MUTED, size=11),
        hovertemplate="<b>%{y}</b><br>Mentions: <b>%{x}</b><extra></extra>",
    ))

    return _theme(fig, "Most Mentioned Keywords")


# =============================================================================
# Score Histogram
# =============================================================================
def make_score_histogram(df: pd.DataFrame) -> Figure:
    """
    Histogram of intelligence score distribution across all staged articles.
    """
    if df is None or df.empty or "intelligence_score" not in df.columns:
        return _empty("No score data")

    fig = px.histogram(
        df, x="intelligence_score", nbins=20,
        color_discrete_sequence=["#C8A96A"],
        labels={"intelligence_score": "Intelligence Score"},
    )

    fig.update_traces(
        marker_line_color=_BG,
        marker_line_width=1,
        opacity=0.85,
        hovertemplate="Score: <b>%{x}</b><br>Articles: <b>%{y}</b><extra></extra>",
    )

    fig.update_layout(bargap=0.06, xaxis=dict(range=[0, 100], dtick=10))
    return _theme(fig, "Score Distribution")
