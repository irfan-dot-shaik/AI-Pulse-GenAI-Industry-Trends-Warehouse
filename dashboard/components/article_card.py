# =============================================================================
# dashboard/components/article_card.py — AI Pulse Dashboard
# =============================================================================
#
# DESIGN: Premium article card using Old Money / Quiet Luxury aesthetic.
# Gold left-border accent on hover. Warm muted badge system.
# No bright colors. Typography-first layout.
#
# =============================================================================

import streamlit as st
import pandas as pd
from dashboard.utils.formatters import (
    format_relative_time,
    format_datetime_display,
    format_keywords,
    truncate_text,
)

# Badge class → CSS class mapping (defined in styles.py)
_BADGE = {
    "Hot Trend":   "badge-hot",
    "High Impact": "badge-high",
    "Trending":    "badge-trend",
    "Normal":      "badge-normal",
}

# Score range → short label (used in compact rows)
_SCORE_LABEL = {
    "Hot Trend":   "Gold",
    "High Impact": "Amber",
    "Trending":    "Green",
    "Normal":      "Stone",
}


def _badge_html(score: int, category: str) -> str:
    """Score badge: category label + numeric score."""
    cls = _BADGE.get(category, "badge-normal")
    return f'<span class="badge {cls}">{category} · {score}</span>'


def _keywords_html(kw_str: str, max_tags: int = 5) -> str:
    """Render keyword tags strip."""
    kws = format_keywords(kw_str)
    if not kws:
        return ""
    tags = "".join(f'<span class="kw-tag">{k}</span>' for k in kws[:max_tags])
    return f'<div style="margin-top:0.55rem; line-height:2;">{tags}</div>'


def render_article_card(row: pd.Series, show_score: bool = True) -> None:
    """
    Render a full-width premium article card.

    Layout (top to bottom):
      ┌─────────────────────────────── [Score Badge] ─┐
      │ Article Title (clickable link)                 │
      │ Source · Published Time                        │
      │ Description preview (160 chars)                │
      │ [keyword] [keyword] [keyword]                  │
      └────────────────────────────── [Read More →] ──┘

    Args:
        row:        pandas Series with stg_ai_news columns.
        show_score: Show the score badge if True.
    """
    title       = str(row.get("title", "Untitled"))
    source      = str(row.get("source", "Unknown Source"))
    description = truncate_text(str(row.get("description", "")), max_chars=200)
    url         = str(row.get("url", "#"))
    published   = row.get("published_at")
    score       = int(row.get("intelligence_score", 0))
    category    = str(row.get("score_category", "Normal"))
    keywords    = str(row.get("keywords_found", ""))

    rel_time  = format_relative_time(published)
    abs_time  = format_datetime_display(published)
    badge     = _badge_html(score, category) if show_score else ""
    kw_html   = _keywords_html(keywords)

    html = f"""
    <div class="article-card">
        <div style="display:flex; justify-content:space-between;
                    align-items:flex-start; gap:0.8rem; margin-bottom:0.5rem;">
            <div class="article-title" style="flex:1;">
                <a href="{url}" target="_blank" rel="noopener">{title}</a>
            </div>
            <div style="flex-shrink:0; padding-top:0.15rem;">{badge}</div>
        </div>
        <div class="article-meta">
            <span style="font-weight:600; color:#A9B1A6;">{source}</span>
            <span style="color:#6B7566; margin:0 0.3rem;">·</span>
            <span title="{abs_time}">{rel_time}</span>
        </div>
        <div class="article-description">{description}</div>
        {kw_html}
        <div style="margin-top:1.2rem;">
            <a href="{url}" target="_blank" rel="noopener"
               style="font-family:'Inter',sans-serif; font-size:0.72rem;
                      font-weight:600; letter-spacing:0.08em; text-transform:uppercase;
                      color:#C8A96A; text-decoration:none;
                      border-bottom:1px solid rgba(200,169,106,0.15);
                      padding-bottom:2px;
                      transition:color 300ms ease, border-color 300ms ease;">
                Read Article →
            </a>
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def render_compact_article_row(row: pd.Series, rank: int = 0) -> None:
    """
    Render a compact one-line ranked article row for the home page top list.

    Layout: [#N] [SCORE] Title — Source · Time

    Args:
        row:  pandas Series with article data.
        rank: 1-based rank number. 0 = no rank shown.
    """
    title    = str(row.get("title", "Untitled"))
    source   = str(row.get("source", "Unknown Source"))
    url      = str(row.get("url", "#"))
    score    = int(row.get("intelligence_score", 0))
    category = str(row.get("score_category", "Normal"))
    relative = format_relative_time(row.get("published_at"))

    badge_cls = _BADGE.get(category, "badge-normal")

    rank_html = (
        f'<span style="font-family:\'Space Grotesk\',monospace; font-size:0.78rem; '
        f'color:#6B7566; font-weight:600; min-width:1.8rem; display:inline-block;">'
        f'#{rank}</span>'
    ) if rank > 0 else ""

    html = f"""
    <div class="article-card" style="padding:0.9rem 1.4rem;">
        <div style="display:flex; align-items:center; gap:0.8rem;">
            {rank_html}
            <span class="badge {badge_cls}" style="min-width:3rem; text-align:center;">
                {score}
            </span>
            <div style="flex:1; min-width:0; overflow:hidden;">
                <a href="{url}" target="_blank" rel="noopener"
                   style="font-family:'Inter',sans-serif; font-size:0.9rem;
                          font-weight:600; color:#F7F5F2; text-decoration:none;
                          white-space:nowrap; overflow:hidden; text-overflow:ellipsis;
                          display:block; transition:color 180ms ease;">
                    {title}
                </a>
                <div style="font-size:0.73rem; color:#6B7566; margin-top:0.2rem;">
                    {source} <span style="margin:0 0.25rem;">·</span> {relative}
                </div>
            </div>
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)
