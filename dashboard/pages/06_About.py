import sys
import os
import streamlit as st

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

st.set_page_config(
    page_title="About | AI Pulse",
    page_icon="◆",
    layout="wide",
    initial_sidebar_state="expanded"
)

from dashboard.components.styles import inject_styles, render_page_header
from dashboard.components.sidebar import render_sidebar
from dashboard.components.footer import render_footer
from dashboard.utils.db_helper import get_engine

inject_styles()
engine = get_engine()
render_sidebar(engine, current_page="About")

render_page_header(
    title="About AI Pulse",
    subtitle="Project background, architecture, and technology stack."
)

# Project Overview
st.markdown("### Project Overview")
st.markdown(
    "**AI Pulse** is a Data Engineering portfolio project built during a 5-week internship. "
    "It simulates a real-world pipeline that automatically collects, validates, scores, and visualizes "
    "Generative AI industry news."
)

st.markdown("---")

# Problem Statement
st.markdown("### Problem Statement")
st.markdown(
    "Analysts and researchers currently spend 3–5 hours per day manually browsing news websites to understand trends "
    "in the Generative AI space. This process is inconsistent, slow, and misses community-driven insights. "
    "AI Pulse automates this by providing a unified, scored, and interactive dashboard."
)

st.markdown("---")

# Architecture Diagram
st.markdown("### Architecture Diagram")
st.markdown("A Medallion Architecture ensures robust separation between raw ingested data and clean analytical data.")
st.code("""
    GNews + HackerNews + Reddit
                ↓
          Ingestion Layer
                ↓
          Raw PostgreSQL
                ↓
    Validation + Transformation + Scoring
                ↓
          Staging Layer
                ↓
          Analytics Layer
                ↓
          Streamlit Dashboard
""", language="text")

st.markdown("---")

# Tech Stack & Data Sources
col1, col2 = st.columns(2, gap="large")

with col1:
    st.markdown("### Tech Stack")
    st.markdown(
        "- **Python 3.12** — Core pipeline\n"
        "- **PostgreSQL 16** — Data warehouse\n"
        "- **SQLAlchemy & Pandas** — ORM and Data Processing\n"
        "- **Streamlit & Plotly** — Interactive UI\n"
        "- **Pytest** — Test-driven development (30 passing tests)"
    )

with col2:
    st.markdown("### Data Sources")
    st.markdown(
        "- **GNews API** — Editorial news\n"
        "- **Hacker News** — Developer sentiment (REST API)\n"
        "- **Reddit** — Community trends (PRAW)"
    )

st.markdown("---")

# Achievements
st.markdown("### Internship Journey")
with st.expander("Phase 1: Foundation", expanded=True):
    st.markdown(
        "- Established the Medallion Architecture.\n"
        "- Created GNews API ingestion client.\n"
        "- Built the PostgreSQL schema."
    )

with st.expander("Phase 2: Processing & Analytics", expanded=True):
    st.markdown(
        "- Built Pandas-based validation and transformation.\n"
        "- Designed the AI Intelligence Scoring heuristic (0-100).\n"
        "- Launched the Streamlit executive dashboard."
    )

with st.expander("Phase 3: Multi-Source Scaling & Production", expanded=True):
    st.markdown(
        "- Added Hacker News & Reddit ingestion.\n"
        "- Implemented concurrent API fetching via `ThreadPoolExecutor`.\n"
        "- Added Source Analytics, polished the executive dashboard UI.\n"
        "- Dockerized the full stack with Docker & Docker Compose.\n"
        "- Achieved 30+ passing automated tests."
    )

st.markdown("---")

# Future Scope
st.markdown("### Future Scope")
st.markdown(
    "- Orchestrating the pipeline with Apache Airflow.\n"
    "- NLP-based sentiment analysis and summarization.\n"
    "- Real-time streaming ingestion with Kafka."
)

st.markdown("---")

# Developer Information
st.markdown("### Developer Information")
st.info(
    "**Shaik Irfan**\n\n"
    "B.Tech CSE - AI & DE\n\n"
    "*Final Internship Showcase — Production Ready Analytics Platform*"
)

render_footer()
