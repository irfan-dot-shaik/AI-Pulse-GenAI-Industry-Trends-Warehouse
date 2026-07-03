# =============================================================================
# dashboard/pages/04_Insights.py — AI Pulse Dashboard
# =============================================================================
# MODULE 7: Insights & Pipeline Intelligence
#
# Answers: What is happening? Why? Is the pipeline healthy? What trends?
#
# Sections:
#   1. Executive Insights    — 6 dynamic insight cards
#   2. Trend Analysis        — 4 charts (score/source/keyword/category trends)
#   3. Pipeline Monitoring   — 6 operational KPI cards
#   4. Data Quality          — 6 quality metric cards + visual bar
#   5. Recommendations       — Auto-generated data-driven narratives
# =============================================================================

import sys, os
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

import streamlit as st

st.set_page_config(
    page_title="Insights — AI Pulse",
    page_icon="◆",
    layout="wide",
    initial_sidebar_state="expanded",
)

from dashboard.utils.db_helper import get_engine, is_db_connected
from dashboard.components.styles import inject_styles, render_page_header, render_section_header
from dashboard.components.sidebar import render_sidebar
from dashboard.components.charts import (
    make_articles_per_day_line,
    make_source_bar,
    make_keyword_bar,
    make_category_donut,
)
from dashboard.utils.formatters import format_number, format_score
from dashboard.components.footer import render_footer
from analytics.queries import (
    get_last_updated_time,
)
from dashboard.utils.cached_queries import (
    cached_avg_score,
    cached_max_score,
    cached_total_articles,
    cached_todays_articles,
    cached_unique_sources,
    cached_sources,
    cached_keyword_freq,
    cached_category_distribution,
    cached_company_mentions,
    cached_data_quality,
    cached_articles_per_day,
    cached_top_scored_articles,
    cached_pipeline_health,
)
from dashboard.utils.error_boundary import error_boundary

inject_styles()
engine = get_engine()
render_sidebar(engine, current_page="Insights")

# ── Connection Guard ──────────────────────────────────────────────────────────
if not is_db_connected(engine):
    st.markdown(
        """<div style="max-width:480px;margin:5rem auto;text-align:center;">
        <div style="font-size:2rem;opacity:0.2;margin-bottom:1rem;">◆</div>
        <div style="font-family:'Cormorant Garamond',serif;font-size:1.7rem;
                    font-weight:600;color:#F7F5F2;margin-bottom:0.5rem;">Database Offline</div>
        <div style="color:#A9B1A6;font-size:0.86rem;">
            Run <code style="color:#C8A96A;">python main.py</code> first.</div>
        </div>""",
        unsafe_allow_html=True,
    )
    st.stop()

render_page_header(
    title="Insights & Intelligence",
    subtitle=(
        "Executive intelligence briefing — dynamic insights, trend analysis, "
        "pipeline health monitoring, and data quality assessment."
    ),
)

with error_boundary("Failed to load insights data. Please check database connectivity."):
    with st.spinner("Compiling executive intelligence..."):
        # ── Pre-fetch shared data (minimise DB round-trips) ───────────────────────────
        avg_score   = cached_avg_score(engine)
        peak_score  = cached_max_score(engine)
        total_arts  = cached_total_articles(engine)
        today_arts  = cached_todays_articles(engine)
        n_sources   = cached_unique_sources(engine)
        src_df      = cached_sources(engine, top_n=10)
        kw_df       = cached_keyword_freq(engine, top_n=12)
        cat_df      = cached_category_distribution(engine)
        companies   = cached_company_mentions(engine)
        top1        = cached_top_scored_articles(engine, limit=1)
        dq          = cached_data_quality(engine)
        health      = cached_pipeline_health(engine)

# Derived values
top_pub     = src_df["source"].iloc[0]  if not src_df.empty else "N/A"
top_pub_n   = int(src_df["article_count"].iloc[0]) if not src_df.empty else 0
top_kw      = kw_df["keyword"].iloc[0]  if not kw_df.empty  else "N/A"
top_kw_n    = int(kw_df["frequency"].iloc[0]) if not kw_df.empty else 0
top_company = companies["company"].iloc[0] if not companies.empty else "N/A"
top_co_n    = int(companies["mentions"].iloc[0]) if not companies.empty else 0
top_title   = str(top1["title"].iloc[0])[:60] + "…" if not top1.empty else "N/A"
daily_avg   = round(total_arts / max(1, 7), 1)  # rough weekly avg


# =============================================================================
# SECTION 1 — Executive Insights
# =============================================================================
render_section_header("Executive Insights")

insights = [
    ("Most Active Publisher",  top_pub,         f"{top_pub_n} articles ingested",    "#C8A96A"),
    ("Top AI Company",         top_company,     f"{top_co_n} mentions across articles", "#C9984A"),
    ("Peak Intelligence",      f"{peak_score}",  top_title,                            "#6E9F67"),
    ("Most Common Keyword",    top_kw.upper(),  f"Appears {top_kw_n} times",          "#A9B1A6"),
    ("Daily Avg. Articles",    f"{daily_avg}",   "Based on current dataset",           "#7A8078"),
    ("Data Quality",           f"{dq['success_rate']}%",  f"{dq['staging_count']} of {dq['raw_count']} passed", "#6E9F67"),
]

cols_i = st.columns(len(insights), gap="medium")
for col, (label, value, ctx, color) in zip(cols_i, insights):
    with col:
        st.markdown(
            f"""
            <div style="background:#1C2721;border:1px solid rgba(200,169,106,0.08);
                        border-radius:12px;padding:1.3rem 1.2rem;
                        border-left:3px solid {color};height:100%;">
                <div style="font-family:'Inter',sans-serif;font-size:0.62rem;
                            font-weight:700;letter-spacing:0.12em;text-transform:uppercase;
                            color:#6B7566;margin-bottom:0.6rem;">{label}</div>
                <div style="font-family:'Space Grotesk',sans-serif;font-size:1.35rem;
                            font-weight:600;color:{color};margin-bottom:0.4rem;
                            line-height:1.2;">{value}</div>
                <div style="font-family:'Inter',sans-serif;font-size:0.74rem;
                            color:#6B7566;line-height:1.5;">{ctx}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


# =============================================================================
# SECTION 2 — Trend Analysis
# =============================================================================
render_section_header("Trend Analysis")

# Row 1: Articles over time + Source distribution
t1, t2 = st.columns(2, gap="large")
with t1:
    trend_df = cached_articles_per_day(engine, days=30)
    st.plotly_chart(make_articles_per_day_line(trend_df), width="stretch",
                    config={"displayModeBar": False})
with t2:
    st.plotly_chart(make_source_bar(src_df), width="stretch",
                    config={"displayModeBar": False})

# Row 2: Keyword trend + Category donut
t3, t4 = st.columns(2, gap="large")
with t3:
    st.plotly_chart(make_keyword_bar(kw_df), width="stretch",
                    config={"displayModeBar": False})
with t4:
    st.plotly_chart(make_category_donut(cat_df), width="stretch",
                    config={"displayModeBar": False})
    # Inline legend
    st.markdown(
        """<div style="font-size:0.72rem;color:#6B7566;line-height:2;text-align:center;">
        <span style="color:#C8A96A;">■</span> Gold
        <span style="color:#C9984A;">■</span> Amber
        <span style="color:#6E9F67;">■</span> Green
        <span style="color:#7A8078;">■</span> Stone</div>""",
        unsafe_allow_html=True,
    )


# =============================================================================
# SECTION 3 — Pipeline Monitoring
# =============================================================================
render_section_header("Pipeline Monitoring")

db_label = "Connected" if health["db_connected"] else "Offline"
last_run = get_last_updated_time(engine)

m1, m2, m3, m4, m5, m6 = st.columns(6, gap="medium")
with m1:
    st.metric("Database",      db_label,                            delta="PostgreSQL")
with m2:
    st.metric("Raw Layer",     format_number(dq["raw_count"]),      delta="raw_ai_news")
with m3:
    st.metric("Staging Layer", format_number(dq["staging_count"]),  delta="stg_ai_news")
with m4:
    st.metric("Success Rate",  f"{dq['success_rate']}%",            delta="Validation pass")
with m5:
    st.metric("Duplicates",    format_number(dq["duplicate_count"]),delta="Duplicate URLs")
with m6:
    st.metric("Last Run",      last_run,                            delta="UTC")


# =============================================================================
# SECTION 4 — Data Quality
# =============================================================================
render_section_header("Data Quality")

q1, q2, q3, q4, q5, q6 = st.columns(6, gap="medium")
with q1:
    st.metric("Valid Articles",    format_number(dq["staging_count"]),  delta="Passed validation")
with q2:
    st.metric("Rejected",         format_number(dq["rejected_count"]), delta="Failed 5 rules")
with q3:
    st.metric("Duplicates",       format_number(dq["duplicate_count"]),delta="URL conflicts")
with q4:
    st.metric("Avg. Description",  f"{dq['avg_desc_length']} chars",   delta="Mean length")
with q5:
    st.metric("Keyword Coverage",  f"{dq['keyword_coverage']}%",       delta="Articles with keywords")
with q6:
    st.metric("Unique Sources",    format_number(n_sources),           delta="Publishers")

# Quality bar visual
bar_pct = min(100, dq["success_rate"])
bar_color = "#6E9F67" if bar_pct >= 80 else ("#C9984A" if bar_pct >= 50 else "#B35C4A")

st.markdown(
    f"""
    <div style="margin:1rem 0;padding:1rem 1.4rem;background:#1C2721;
                border:1px solid rgba(200,169,106,0.08);border-radius:10px;">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:0.5rem;">
            <span style="font-family:'Inter',sans-serif;font-size:0.72rem;font-weight:700;
                         letter-spacing:0.1em;text-transform:uppercase;color:#6B7566;">
                Pipeline Success Rate
            </span>
            <span style="font-family:'Space Grotesk',sans-serif;font-size:0.88rem;
                         font-weight:600;color:{bar_color};">
                {bar_pct}%
            </span>
        </div>
        <div style="background:rgba(200,169,106,0.06);border-radius:4px;height:6px;overflow:hidden;">
            <div style="width:{bar_pct}%;height:100%;background:{bar_color};border-radius:4px;
                        transition:width 0.5s ease;"></div>
        </div>
        <div style="font-family:'Inter',sans-serif;font-size:0.74rem;color:#6B7566;margin-top:0.5rem;">
            {dq['staging_count']} of {dq['raw_count']} articles passed validation ·
            {dq['rejected_count']} rejected · {dq['duplicate_count']} duplicate URL(s) detected
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


# =============================================================================
# SECTION 5 — Recommendations
# =============================================================================
render_section_header("Recommendations")

# Build data-driven recommendation narratives
recs = []

# Company dominance
if not companies.empty:
    top_c = companies.iloc[0]
    recs.append({
        "text": f"{top_c['company']} dominated coverage with {int(top_c['mentions'])} mentions across all staged articles.",
        "type": "insight",
    })

# Score quality assessment
if avg_score >= 60:
    recs.append({
        "text": f"Coverage quality is strong — average Intelligence Score is {avg_score:.0f}/100, indicating high-relevance AI content.",
        "type": "positive",
    })
elif avg_score >= 40:
    recs.append({
        "text": f"Average Intelligence Score is {avg_score:.0f}/100. Consider adding premium AI-focused sources to improve quality.",
        "type": "neutral",
    })
else:
    recs.append({
        "text": f"Average Intelligence Score is {avg_score:.0f}/100 — below target. Review search keywords and source list.",
        "type": "warning",
    })

# Publisher diversity
if n_sources >= 5:
    recs.append({
        "text": f"Source diversity is healthy — {n_sources} distinct publishers, led by {top_pub}.",
        "type": "positive",
    })
else:
    recs.append({
        "text": f"Only {n_sources} source(s) detected. Consider broadening the search to improve coverage diversity.",
        "type": "warning",
    })

# Keyword coverage
if dq["keyword_coverage"] >= 80:
    recs.append({
        "text": f"{dq['keyword_coverage']}% of articles matched at least one AI keyword — strong topic alignment.",
        "type": "positive",
    })
else:
    recs.append({
        "text": f"Keyword coverage is {dq['keyword_coverage']}%. Some articles may not be AI-relevant. Review the keyword dictionary.",
        "type": "neutral",
    })

# Data quality
if dq["success_rate"] >= 90:
    recs.append({
        "text": f"Pipeline health is excellent — {dq['success_rate']}% of raw articles passed all 5 validation rules.",
        "type": "positive",
    })
elif dq["rejected_count"] > 0:
    recs.append({
        "text": f"{dq['rejected_count']} article(s) were rejected by the validator. This is normal — the 5 quality rules ensure only clean data enters staging.",
        "type": "neutral",
    })

# Top keyword
if top_kw != "N/A":
    recs.append({
        "text": f'Most discussed topic is "{top_kw}" with {top_kw_n} occurrences — this reflects current industry focus.',
        "type": "insight",
    })

# Render recommendation cards
_REC_COLORS = {
    "positive": "#6E9F67",
    "neutral":  "#C9984A",
    "warning":  "#B35C4A",
    "insight":  "#C8A96A",
}

for i, rec in enumerate(recs):
    accent = _REC_COLORS.get(rec["type"], "#A9B1A6")
    st.markdown(
        f"""
        <div style="background:#1C2721;border:1px solid rgba(200,169,106,0.06);
                    border-radius:10px;padding:1rem 1.4rem;margin-bottom:0.55rem;
                    border-left:3px solid {accent};
                    transition:transform 180ms ease;">
            <div style="font-family:'Inter',sans-serif;font-size:0.86rem;
                        color:#A9B1A6;line-height:1.65;">
                {rec['text']}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


render_footer()
