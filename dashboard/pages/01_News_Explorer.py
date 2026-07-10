# =============================================================================
# dashboard/pages/01_News_Explorer.py — AI Pulse Dashboard
# =============================================================================
#
# MODULE 4: News Explorer
#
# PURPOSE:
#   A full-featured search, filter, and browse interface for all articles
#   in the stg_ai_news staging table. Think of it as the analyst's workspace.
#
# FEATURES:
#   ✔ Keyword search (title + description, case-insensitive)
#   ✔ Filter by source (dropdown from live data)
#   ✔ Filter by score category (Hot Trend / High Impact / Trending / Normal)
#   ✔ Filter by intelligence score range (slider)
#   ✔ Sort by newest / oldest / highest score
#   ✔ Pagination (configurable page size)
#   ✔ Article count with active filter summary
#   ✔ Clickable title → opens original article
#   ✔ "Read Article →" link on every card
#   ✔ Loading state (Streamlit spinner)
#   ✔ Empty state (no results)
#   ✔ No-database state (graceful error)
#   ✔ Filter reset button
#
# DESIGN:
#   Old Money / Quiet Luxury — forest green, warm gold, muted stone.
#   Filter panel above the article grid, not in sidebar (cleaner UX).
#
# ARCHITECTURE:
#   - Reuses analytics.queries.search_articles() — no duplicate SQL
#   - Reuses cached db engine from dashboard.utils.db_helper
#   - Reuses all styled components from dashboard.components.*
#   - Pagination is pure Python — no extra DB query per page
#
# =============================================================================

import sys
import os

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

import streamlit as st

st.set_page_config(
    page_title="News Explorer — AI Pulse",
    page_icon="◆",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Project imports ───────────────────────────────────────────────────────────
from dashboard.utils.db_helper import get_engine, is_db_connected
from dashboard.components.sidebar import render_sidebar
from dashboard.components.article_card import render_article_card
from dashboard.components.footer import render_footer
from dashboard.utils.error_boundary import error_boundary
from analytics.queries import search_articles
from dashboard.utils.cached_queries import cached_all_sources
from dashboard.utils.formatters import format_number
from dashboard.components.styles import inject_styles, render_page_header

# ── Design System ─────────────────────────────────────────────────────────────
inject_styles()

# ── Database ──────────────────────────────────────────────────────────────────
engine = get_engine()
render_sidebar(engine, current_page="Explorer")

# ── Connection Guard ──────────────────────────────────────────────────────────
if not is_db_connected(engine):
    st.markdown(
        """
        <div style="max-width:480px; margin:5rem auto; text-align:center;
                    font-family:'Inter',sans-serif;">
            <div style="font-size:2.2rem;opacity:0.2;margin-bottom:1rem;">◆</div>
            <div style="font-family:'Cormorant Garamond',serif;font-size:1.7rem;
                        font-weight:600;color:#F7F5F2;margin-bottom:0.5rem;">
                Database Offline
            </div>
            <div style="color:#A9B1A6;font-size:0.86rem;line-height:1.7;">
                Please start PostgreSQL and run
                <code style="color:#C8A96A;">python main.py</code>
                before using the Explorer.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.stop()

# ── Page Header ───────────────────────────────────────────────────────────────
render_page_header(
    title="News Explorer",
    subtitle=(
        "Search, filter and browse every article in the staging warehouse. "
        "Combine keyword search with source, category, and score filters."
    ),
)

# =============================================================================
# =============================================================================
# All filters live above the results.
# Using st.columns() for horizontal layout avoids sidebar clutter.
# =============================================================================

fc1, fc2, fc3, fc4, fc5 = st.columns([4, 3, 3, 3, 2], gap="medium")

with fc1:
    keyword = st.text_input(
        "Search",
        placeholder="OpenAI, GPT-4, Gemini…",
        label_visibility="visible",
        key="explorer_keyword",
    )

# Fetch available sources for the dropdown (cached in session state)
if "explorer_sources" not in st.session_state:
    with error_boundary("Failed to load source list."):
        st.session_state["explorer_sources"] = cached_all_sources(engine)

sources_list = ["All Sources"] + st.session_state["explorer_sources"]

with fc2:
    source_choice = st.selectbox(
        "Source",
        options=sources_list,
        key="explorer_source",
    )

with fc3:
    category_choice = st.selectbox(
        "Score Category",
        options=["All Categories", "Hot Trend", "High Impact", "Trending", "Normal"],
        key="explorer_category",
    )

with fc4:
    sort_choice = st.selectbox(
        "Sort By",
        options=["Newest First", "Oldest First", "Highest Score"],
        key="explorer_sort",
    )

with fc5:
    st.html("<div style='height:1.68rem;'></div>")
    reset = st.button("Reset", key="explorer_reset", use_container_width=True)

# Score filter — full-width slider below the row
score_min, score_max = st.slider(
    "Intelligence Score Range",
    min_value=0, max_value=100,
    value=(0, 100),
    key="explorer_score_range",
    help="Filter articles by their AI Intelligence Score (0 = weakest, 100 = strongest).",
)


# ── Handle Reset ──────────────────────────────────────────────────────────────
if reset:
    for k in ["explorer_keyword", "explorer_source", "explorer_category",
              "explorer_sort", "explorer_score_range", "explorer_page"]:
        if k in st.session_state:
            del st.session_state[k]
    st.rerun()

# ── Map UI choices → query parameters ────────────────────────────────────────
_SORT_MAP = {
    "Newest First":  "newest",
    "Oldest First":  "oldest",
    "Highest Score": "score",
}

kw_clean      = keyword.strip()
src_clean     = "" if source_choice == "All Sources" else source_choice
cat_clean     = "" if category_choice == "All Categories" else category_choice
sort_key      = _SORT_MAP[sort_choice]

# =============================================================================
# DATA FETCH
# =============================================================================
# Fetch up to 200 results then paginate in Python.
# This avoids a new DB query on every page flip (fast for our dataset size).
# For very large datasets (>10k rows), server-side pagination via OFFSET
# would be the production choice.
# =============================================================================

with error_boundary("Search failed. Please check your database connection."):
    with st.spinner("Searching warehouse..."):
        raw_df = search_articles(
            engine,
            keyword=kw_clean,
            source_filter=src_clean,
            score_filter=cat_clean,
            sort_by=sort_key,
            limit=200,
        )

# Apply score range filter in Python (no extra SQL round-trip)
if not raw_df.empty and "intelligence_score" in raw_df.columns:
    raw_df = raw_df[
        (raw_df["intelligence_score"] >= score_min) &
        (raw_df["intelligence_score"] <= score_max)
    ]

total_results = len(raw_df)

# =============================================================================
# RESULTS HEADER
# =============================================================================

# Build a human-readable active filter summary
active_filters = []
if kw_clean:
    active_filters.append(f'"{kw_clean}"')
if src_clean:
    active_filters.append(src_clean)
if cat_clean:
    active_filters.append(cat_clean)
if score_min > 0 or score_max < 100:
    active_filters.append(f"Score {score_min}–{score_max}")

filter_summary = (
    " · ".join(active_filters) if active_filters else "All articles"
)

st.markdown(
    f"""
    <div style="display:flex; justify-content:space-between; align-items:baseline;
                margin: 1.2rem 0 0.8rem; padding-bottom:0.8rem;
                border-bottom:1px solid rgba(200,169,106,0.08);">
        <div style="font-family:'Space Grotesk',sans-serif; font-size:1.6rem;
                    font-weight:600; color:#F7F5F2; letter-spacing:-0.02em;">
            {format_number(total_results)}
            <span style="font-size:0.88rem; font-weight:400;
                         color:#A9B1A6; margin-left:0.4rem;">articles</span>
        </div>
        <div style="font-family:'Inter',sans-serif; font-size:0.76rem;
                    color:#6B7566; letter-spacing:0.02em;">
            {filter_summary}
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# =============================================================================
# EMPTY STATE
# =============================================================================

if raw_df.empty:
    has_filters = bool(kw_clean or src_clean or cat_clean
                       or score_min > 0 or score_max < 100)

    if has_filters:
        empty_title = "No Matching Articles"
        empty_sub   = (
            "Try broadening your search — remove a filter, "
            "reduce the score range, or search for a different keyword."
        )
    else:
        empty_title = "Warehouse is Empty"
        empty_sub   = (
            "No articles in the staging table. "
            "Run <code style='color:#C8A96A;'>python main.py</code> to ingest data."
        )

    st.markdown(
        f"""
        <div class="empty-state" style="padding:5rem 2rem;">
            <span class="empty-state-icon">◇</span>
            <div class="empty-state-title">{empty_title}</div>
            <div class="empty-state-sub">{empty_sub}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.stop()

# =============================================================================
# PAGINATION
# =============================================================================
# Pure Python pagination: slice the DataFrame by page.
# PAGE_SIZE controls articles per page.
# st.session_state["explorer_page"] persists across filter changes.
# =============================================================================

PAGE_SIZE = 10

# Reset to page 1 when any filter changes
filter_sig = f"{kw_clean}|{src_clean}|{cat_clean}|{sort_key}|{score_min}|{score_max}"
if st.session_state.get("_explorer_filter_sig") != filter_sig:
    st.session_state["_explorer_filter_sig"] = filter_sig
    st.session_state["explorer_page"] = 1

current_page = st.session_state.get("explorer_page", 1)
total_pages  = max(1, (total_results + PAGE_SIZE - 1) // PAGE_SIZE)
current_page = max(1, min(current_page, total_pages))

# Slice for current page
start_idx = (current_page - 1) * PAGE_SIZE
end_idx   = min(start_idx + PAGE_SIZE, total_results)
page_df   = raw_df.iloc[start_idx:end_idx]

# =============================================================================
# ARTICLE CARDS
# =============================================================================

for _, row in page_df.iterrows():
    render_article_card(row, show_score=True)

# =============================================================================
# PAGINATION CONTROLS
# =============================================================================

st.html("<div style='height:1.2rem;'></div>")

if total_pages > 1:
    # Range of page numbers to show (show ±2 around current page)
    show_range = sorted(set(
        [1, total_pages]
        + list(range(max(1, current_page - 2), min(total_pages, current_page + 2) + 1))
    ))

    pag_cols = st.columns(len(show_range) + 4, gap="small")
    col_idx  = 0

    # Prev button
    with pag_cols[col_idx]:
        if current_page > 1:
            if st.button("←", key="pg_prev"):
                st.session_state["explorer_page"] = current_page - 1
                st.rerun()
    col_idx += 1

    # Page number buttons
    prev_num = None
    for pnum in show_range:
        if prev_num is not None and pnum > prev_num + 1:
            with pag_cols[col_idx]:
                st.html("<div style='text-align:center;color:#6B7566;padding-top:0.45rem;'>…</div>")
            col_idx += 1
        with pag_cols[col_idx]:
            is_cur = pnum == current_page
            label  = f"**{pnum}**" if is_cur else str(pnum)
            if st.button(label, key=f"pg_{pnum}"):
                st.session_state["explorer_page"] = pnum
                st.rerun()
        col_idx += 1
        prev_num = pnum

    # Next button
    with pag_cols[col_idx]:
        if current_page < total_pages:
            if st.button("→", key="pg_next"):
                st.session_state["explorer_page"] = current_page + 1
                st.rerun()

    # Page info
    st.markdown(
        f"""
        <div style="text-align:center; margin-top:0.6rem;
                    font-family:'Inter',sans-serif; font-size:0.72rem; color:#6B7566;">
            Page {current_page} of {total_pages}
            &nbsp;·&nbsp;
            Showing {start_idx + 1}–{end_idx} of {format_number(total_results)} articles
        </div>
        """,
        unsafe_allow_html=True,
    )


render_footer()
