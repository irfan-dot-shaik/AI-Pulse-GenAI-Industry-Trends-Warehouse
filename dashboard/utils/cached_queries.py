# =============================================================================
# dashboard/utils/cached_queries.py — AI Pulse Dashboard
# =============================================================================
#
# PURPOSE:
#   Thin caching wrapper around analytics.queries functions.
#   Uses @st.cache_data(ttl=300) so the same query isn't repeated
#   within a 5-minute window. This dramatically improves page load
#   performance without changing the analytics layer.
#
# WHY A SEPARATE MODULE:
#   analytics.queries.py is used by both Streamlit and non-Streamlit
#   contexts (main.py, scripts). Putting @st.cache_data on those
#   functions would break non-Streamlit usage. This module isolates
#   the Streamlit-specific caching.
#
# =============================================================================

import streamlit as st
import pandas as pd
from sqlalchemy.engine import Engine


@st.cache_data(ttl=300, show_spinner=False)
def cached_total_articles(_engine: Engine) -> int:
    from analytics.queries import get_total_article_count
    return get_total_article_count(_engine)


@st.cache_data(ttl=300, show_spinner=False)
def cached_todays_articles(_engine: Engine) -> int:
    from analytics.queries import get_todays_article_count
    return get_todays_article_count(_engine)


@st.cache_data(ttl=300, show_spinner=False)
def cached_unique_sources(_engine: Engine) -> int:
    from analytics.queries import get_unique_source_count
    return get_unique_source_count(_engine)


@st.cache_data(ttl=300, show_spinner=False)
def cached_avg_score(_engine: Engine) -> float:
    from analytics.queries import get_average_intelligence_score
    return get_average_intelligence_score(_engine)


@st.cache_data(ttl=300, show_spinner=False)
def cached_max_score(_engine: Engine) -> int:
    from analytics.queries import get_max_intelligence_score
    return get_max_intelligence_score(_engine)


@st.cache_data(ttl=300, show_spinner=False)
def cached_category_distribution(_engine: Engine) -> pd.DataFrame:
    from analytics.queries import get_score_category_distribution
    return get_score_category_distribution(_engine)


@st.cache_data(ttl=300, show_spinner=False)
def cached_pipeline_health(_engine: Engine) -> dict:
    from analytics.queries import get_pipeline_health
    return get_pipeline_health(_engine)


@st.cache_data(ttl=300, show_spinner=False)
def cached_data_quality(_engine: Engine) -> dict:
    from analytics.queries import get_data_quality_stats
    return get_data_quality_stats(_engine)


@st.cache_data(ttl=300, show_spinner=False)
def cached_company_mentions(_engine: Engine) -> pd.DataFrame:
    from analytics.queries import get_company_mentions
    return get_company_mentions(_engine)


@st.cache_data(ttl=300, show_spinner=False)
def cached_sources(_engine: Engine, top_n: int = 10) -> pd.DataFrame:
    from analytics.queries import get_articles_per_source
    return get_articles_per_source(_engine, top_n=top_n)


@st.cache_data(ttl=300, show_spinner=False)
def cached_keyword_freq(_engine: Engine, top_n: int = 12) -> pd.DataFrame:
    from analytics.queries import get_keyword_frequency
    return get_keyword_frequency(_engine, top_n=top_n)


@st.cache_data(ttl=300, show_spinner=False)
def cached_all_sources(_engine: Engine) -> list[str]:
    from analytics.queries import get_all_sources
    return get_all_sources(_engine)


@st.cache_data(ttl=300, show_spinner=False)
def cached_articles_per_day(_engine: Engine, days: int = 30) -> pd.DataFrame:
    from analytics.queries import get_articles_per_day
    return get_articles_per_day(_engine, days=days)


@st.cache_data(ttl=300, show_spinner=False)
def cached_top_scored_articles(_engine: Engine, limit: int = 10) -> pd.DataFrame:
    from analytics.queries import get_top_scored_articles
    return get_top_scored_articles(_engine, limit=limit)
