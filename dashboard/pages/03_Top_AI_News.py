# =============================================================================
# dashboard/pages/03_Top_AI_News.py — AI Pulse Dashboard
# =============================================================================
# MODULE 6: Top AI News & Executive Insights
#
# The flagship page. Showcases the highest-quality AI news from the pipeline.
#
# Sections:
#   1. Executive Summary     — 5 KPI cards (scores + category counts)
#   2. Top AI News           — Top 10 ranked articles, filterable
#   3. Trending Companies    — Company mention bars
#   4. Executive Insights    — Auto-generated insight cards
#   5. Quick Filters         — Search, source, category, sort (above Section 2)
# =============================================================================

import sys, os
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

import streamlit as st

st.set_page_config(
    page_title="Top AI News — AI Pulse",
    page_icon="◆",
    layout="wide",
    initial_sidebar_state="expanded",
)

from dashboard.utils.db_helper import get_engine, is_db_connected
from dashboard.components.styles import inject_styles, render_page_header, render_section_header
from dashboard.components.sidebar import render_sidebar
from dashboard.components.article_card import render_article_card
from dashboard.components.footer import render_footer
from dashboard.utils.error_boundary import error_boundary
from dashboard.utils.formatters import format_number, format_score
from analytics.queries import (
    get_top_scored_articles,
    search_articles,
)
from dashboard.utils.cached_queries import (
    cached_avg_score,
    cached_max_score,
    cached_category_distribution,
    cached_sources,
    cached_keyword_freq,
    cached_all_sources,
    cached_company_mentions,
)

inject_styles()
engine = get_engine()
render_sidebar(engine, current_page="Top AI News")

# ── Connection Guard ──────────────────────────────────────────────────────────
if not is_db_connected(engine):
    st.markdown(
        """<div style="max-width:480px;margin:5rem auto;text-align:center;font-family:'Inter',sans-serif;">
        <div style="font-size:2rem;opacity:0.2;margin-bottom:1rem;">◆</div>
        <div style="font-family:'Cormorant Garamond',serif;font-size:1.7rem;
                    font-weight:600;color:#F7F5F2;margin-bottom:0.5rem;">Database Offline</div>
        <div style="color:#A9B1A6;font-size:0.86rem;">
            Run <code style="color:#C8A96A;">python main.py</code> first.
        </div></div>""",
        unsafe_allow_html=True,
    )
    st.stop()

# ── Page Header ───────────────────────────────────────────────────────────────
render_page_header(
    title="Top AI News",
    subtitle=(
        "The highest-intelligence articles curated by the pipeline — scored, ranked, "
        "and ready for executive briefing."
    ),
)

# =============================================================================
# SECTION 1 — Executive Summary
# =============================================================================
render_section_header("Executive Summary")

with error_boundary("Failed to load Top AI News data. Please check database connectivity."):
    with st.spinner("Ranking articles..."):
        avg_score  = cached_avg_score(engine)
        peak_score = cached_max_score(engine)
        
        # Derive category counts from existing function
        cat_df     = cached_category_distribution(engine)
cat_map    = dict(zip(cat_df["score_category"], cat_df["article_count"])) if not cat_df.empty else {}

hot_count    = cat_map.get("Hot Trend",   0)
high_count   = cat_map.get("High Impact", 0)
trend_count  = cat_map.get("Trending",    0)

k1, k2, k3, k4, k5 = st.columns(5, gap="medium")
with k1:
    st.metric("Peak Score",       f"{peak_score} / 100", delta="Highest article")
with k2:
    st.metric("Avg. Intelligence", format_score(avg_score), delta="All articles")
with k3:
    st.metric("Hot Trend",        format_number(hot_count),   delta="Score 90–100")
with k4:
    st.metric("High Impact",      format_number(high_count),  delta="Score 75–89")
with k5:
    st.metric("Trending",         format_number(trend_count), delta="Score 50–74")

# =============================================================================
# SECTION 5 — Quick Filters  (placed before Section 2 for UX flow)
# =============================================================================
render_section_header("Quick Filters")
qf1, qf2, qf3, qf4, qf5 = st.columns([4, 3, 3, 3, 2], gap="medium")

with qf1:
    kw = st.text_input("Search", placeholder="OpenAI, Claude, Gemini…",
                       key="top_kw")
with qf2:
    if "top_sources" not in st.session_state:
        st.session_state["top_sources"] = cached_all_sources(engine)
    src = st.selectbox("Source",
                       ["All Sources"] + st.session_state["top_sources"],
                       key="top_src")
with qf3:
    cat = st.selectbox("Category",
                       ["All", "Hot Trend", "High Impact", "Trending", "Normal"],
                       key="top_cat")
with qf4:
    sort_ui = st.selectbox("Sort By",
                           ["Highest Score", "Newest First"],
                           key="top_sort")
with qf5:
    st.html("<div style='height:1.68rem;'></div>")
    if st.button("Reset", key="top_reset", use_container_width=True):
        for k in ["top_kw","top_src","top_cat","top_sort"]:
            st.session_state.pop(k, None)
        st.rerun()


# Resolve filter values
kw_val  = kw.strip()
src_val = "" if src == "All Sources" else src
cat_val = "" if cat == "All" else cat
sort_val = "score" if sort_ui == "Highest Score" else "newest"

articles_df = search_articles(
    engine,
    keyword=kw_val,
    source_filter=src_val,
    score_filter=cat_val,
    sort_by=sort_val,
    limit=10,
)

# =============================================================================
# SECTION 2 — Top AI News
# =============================================================================
render_section_header("Top AI News")

if articles_df.empty:
    st.markdown(
        """<div class="empty-state"><span class="empty-state-icon">◇</span>
        <div class="empty-state-title">No Matching Articles</div>
        <div class="empty-state-sub">Try adjusting your filters or run the pipeline.</div>
        </div>""",
        unsafe_allow_html=True,
    )
else:
    count_label = format_number(len(articles_df))
    extra_text = f"· <strong style='color:#C8A96A;'>{kw_val}</strong>" if kw_val else ""
    st.html(
        f"""<div style="font-family:'Space Grotesk',sans-serif;font-size:0.78rem;
                    color:#6B7566;margin-bottom:1rem;">
            Showing {count_label} article{'s' if len(articles_df) != 1 else ''} {extra_text}
        </div>"""
    )
    for _, row in articles_df.iterrows():
        render_article_card(row, show_score=True)

# =============================================================================
# SECTION 3 — Trending Companies
# =============================================================================
render_section_header("Trending Companies")

companies_df = cached_company_mentions(engine)

if companies_df.empty:
    st.markdown(
        '<div style="color:#6B7566;font-size:0.86rem;padding:1rem 0;">No company data yet.</div>',
        unsafe_allow_html=True,
    )
else:
    max_m = companies_df["mentions"].max() or 1
    n_cols = min(len(companies_df), 5)
    cols   = st.columns(n_cols, gap="medium")

    for i, (_, row) in enumerate(companies_df.head(n_cols * 2).iterrows()):
        company  = str(row["company"])
        mentions = int(row["mentions"])
        pct      = mentions / max_m        # 0.0 → 1.0
        bar_w    = max(8, int(pct * 100))  # percent width of the fill bar

        # Pick colour by rank
        if i == 0:
            bar_color = "#C8A96A"  # gold — top company
        elif i == 1:
            bar_color = "#C9984A"  # amber
        elif i == 2:
            bar_color = "#6E9F67"  # forest green
        else:
            bar_color = "#7A8078"  # stone

        col_idx = i % n_cols
        with cols[col_idx]:
            st.markdown(
                f"""
                <div style="background:#1C2721;border:1px solid rgba(200,169,106,0.08);
                            border-radius:10px;padding:1.1rem 1.2rem;margin-bottom:0.7rem;">
                    <div style="font-family:'Inter',sans-serif;font-size:0.68rem;
                                font-weight:700;letter-spacing:0.08em;text-transform:uppercase;
                                color:#6B7566;margin-bottom:0.4rem;">#{i+1}</div>
                    <div style="font-family:'Cormorant Garamond',serif;font-size:1.25rem;
                                font-weight:600;color:#F7F5F2;margin-bottom:0.6rem;">
                        {company}
                    </div>
                    <div style="background:rgba(200,169,106,0.06);border-radius:4px;
                                height:4px;margin-bottom:0.5rem;overflow:hidden;">
                        <div style="width:{bar_w}%;height:100%;
                                    background:{bar_color};border-radius:4px;
                                    transition:width 0.4s ease;"></div>
                    </div>
                    <div style="font-family:'Space Grotesk',sans-serif;font-size:0.8rem;
                                color:{bar_color};font-weight:600;">
                        {mentions} mention{'s' if mentions != 1 else ''}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

# =============================================================================
# SECTION 4 — Executive Insights
# =============================================================================
render_section_header("Executive Insights")

# Derive insights from already-fetched data (no extra DB queries)
src_df      = cached_sources(engine, top_n=1)
kw_df       = cached_keyword_freq(engine, top_n=1)
top_article = get_top_scored_articles(engine, limit=1)

top_pub     = src_df["source"].iloc[0]        if not src_df.empty    else "N/A"
top_kw      = kw_df["keyword"].iloc[0]        if not kw_df.empty     else "N/A"
top_art_title = (
    str(top_article["title"].iloc[0])[:72] + "…"
    if not top_article.empty else "N/A"
)
top_art_score = (
    int(top_article["intelligence_score"].iloc[0])
    if not top_article.empty else 0
)
top_company = (
    str(companies_df["company"].iloc[0])
    if not companies_df.empty else "N/A"
)

insights = [
    {
        "label":   "Most Discussed Company",
        "value":   top_company,
        "context": f"Appears most in keyword matches across all articles",
        "color":   "#C8A96A",
    },
    {
        "label":   "Highest Scoring Article",
        "value":   f"{top_art_score} / 100",
        "context": top_art_title,
        "color":   "#C9984A",
    },
    {
        "label":   "Most Active Publisher",
        "value":   top_pub,
        "context": "Highest article volume in the staging warehouse",
        "color":   "#6E9F67",
    },
    {
        "label":   "Most Common Keyword",
        "value":   top_kw.upper(),
        "context": "Appears most frequently across all article keywords",
        "color":   "#A9B1A6",
    },
    {
        "label":   "Avg. Intelligence Score",
        "value":   format_score(avg_score),
        "context": "Mean score across all validated and staged articles",
        "color":   "#7A8078",
    },
]

i_cols = st.columns(len(insights), gap="medium")
for col, ins in zip(i_cols, insights):
    with col:
        st.markdown(
            f"""
            <div style="background:#1C2721;border:1px solid rgba(200,169,106,0.08);
                        border-radius:12px;padding:1.4rem 1.3rem;height:100%;
                        border-left:3px solid {ins['color']};">
                <div style="font-family:'Inter',sans-serif;font-size:0.64rem;
                            font-weight:700;letter-spacing:0.12em;text-transform:uppercase;
                            color:#6B7566;margin-bottom:0.7rem;">
                    {ins['label']}
                </div>
                <div style="font-family:'Space Grotesk',sans-serif;font-size:1.4rem;
                            font-weight:600;color:{ins['color']};
                            margin-bottom:0.5rem;line-height:1.2;">
                    {ins['value']}
                </div>
                <div style="font-family:'Inter',sans-serif;font-size:0.76rem;
                            color:#6B7566;line-height:1.55;">
                    {ins['context']}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


render_footer()
