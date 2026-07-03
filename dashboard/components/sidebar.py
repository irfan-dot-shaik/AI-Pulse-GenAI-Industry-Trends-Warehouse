# =============================================================================
# dashboard/components/sidebar.py — AI Pulse Dashboard
# =============================================================================
#
# DESIGN: Old Money / Quiet Luxury sidebar.
# Minimal, typographic, warm forest green with gold accents.
# No emojis in nav — replaced with elegant geometric indicators.
#
# =============================================================================

import streamlit as st
from sqlalchemy.engine import Engine

from analytics.queries import get_pipeline_health
from dashboard.utils.db_helper import is_db_connected
from dashboard.utils.formatters import format_number


def render_sidebar(engine: Engine, current_page: str = "Home") -> None:
    """
    Render the premium left sidebar: branding, navigation, pipeline health,
    database status, and project footer.

    Args:
        engine:       SQLAlchemy engine from db_helper.get_engine().
        current_page: Active page name for nav highlighting.
                      One of: "Home", "Explorer", "Analytics", "Top AI News", "Insights".
    """
    with st.sidebar:

        # ── Branding ─────────────────────────────────────────────────
        st.markdown(
            """
            <div style="padding: 1.8rem 1rem 1.2rem; border-bottom: 1px solid rgba(200,169,106,0.10);">
                <div style="font-family:'Cormorant Garamond',Georgia,serif;
                            font-size: 1.55rem; font-weight: 600;
                            color: #F7F5F2; letter-spacing: -0.01em;
                            line-height: 1.1; margin-bottom: 0.25rem;">
                    AI Pulse
                </div>
                <div style="font-family:'Inter',sans-serif;
                            font-size: 0.68rem; font-weight: 600;
                            color: #C8A96A; letter-spacing: 0.12em;
                            text-transform: uppercase;">
                    GenAI Industry Intelligence
                </div>
                <div style="font-family:'Inter',sans-serif;
                            font-size: 0.72rem; color: #6B7566;
                            margin-top: 0.5rem; line-height: 1.5;">
                    Data Engineering · Week 2
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # ── Navigation ───────────────────────────────────────────────
        st.markdown(
            """
            <div style="font-family:'Inter',sans-serif; font-size:0.65rem;
                        font-weight:700; letter-spacing:0.12em; text-transform:uppercase;
                        color:#6B7566; padding: 1.2rem 1rem 0.5rem;">
                Navigate
            </div>
            """,
            unsafe_allow_html=True,
        )

        nav_items = [
            ("Home",        "Overview"),
            ("Explorer",    "News Explorer"),
            ("Analytics",   "Analytics"),
            ("Top AI News", "Top AI News"),
            ("Insights",    "Insights"),
        ]

        for page_key, page_label in nav_items:
            is_active = page_key == current_page
            bg        = "rgba(200,169,106,0.07)" if is_active else "transparent"
            text_color = "#C8A96A" if is_active else "#A9B1A6"
            border_l  = "2px solid #C8A96A" if is_active else "2px solid transparent"
            weight    = "600" if is_active else "400"

            st.markdown(
                f"""
                <div style="display:flex; align-items:center;
                            padding: 0.6rem 1rem; margin: 0.15rem 0;
                            border-left: {border_l};
                            background: {bg};
                            transition: all 300ms ease; cursor:pointer;">
                    <span style="font-family:'Inter',sans-serif;
                                 font-size:0.86rem; font-weight:{weight};
                                 color:{text_color}; letter-spacing:0.02em;">
                        {page_label}
                    </span>
                </div>
                """,
                unsafe_allow_html=True,
            )

        # ── Database Status & Health ─────────────────────────────────
        db_ok = is_db_connected(engine)

        st.markdown(
            f"""
            <div style="border-top: 1px solid rgba(200,169,106,0.10);
                        margin-top: 2rem; padding-top: 1rem;">
                <div style="font-family:'Inter',sans-serif; font-size:0.65rem;
                            font-weight:700; letter-spacing:0.12em; text-transform:uppercase;
                            color:#6B7566; margin-bottom:0.7rem;">
                    System Status
                </div>
                <div style="display:flex; align-items:center; gap:0.5rem; margin-bottom:0.8rem;">
                    <span class="status-dot {'online' if db_ok else 'offline'}"></span>
                    <span style="font-family:'Inter',sans-serif; font-size:0.78rem;
                                 color:{'#6E9F67' if db_ok else '#B35C4A'}; font-weight:500;">
                        {'PostgreSQL Connected' if db_ok else 'Database Offline'}
                    </span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if db_ok and engine is not None:
            health = get_pipeline_health(engine)
            st.markdown(
                f"""
                <div style="margin-bottom: 2rem;">
                    <div class="health-card" style="border:none; background:transparent;">
                        <div class="health-row" style="padding:0.3rem 0; border:none; background:transparent;">
                            <span class="label">Raw Layer</span>
                            <span class="value">{format_number(health['raw_count'])}</span>
                        </div>
                        <div class="health-row" style="padding:0.3rem 0; border:none; background:transparent;">
                            <span class="label">Staging</span>
                            <span class="value">{format_number(health['staging_count'])}</span>
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        # ── Footer / Developer ───────────────────────────────────────
        last_run = health['last_run'] if (db_ok and engine is not None) else "Unknown"
        
        st.markdown(
            f"""
            <div style="border-top: 1px solid rgba(200,169,106,0.10);
                        margin-top: 2rem; padding: 1rem 0;
                        background: transparent;">
                <div style="font-family:'Inter',sans-serif; font-size:0.65rem;
                            font-weight:700; letter-spacing:0.12em; text-transform:uppercase;
                            color:#6B7566; margin-bottom:0.7rem;">
                    Developer
                </div>
                <div style="font-family:'Inter',sans-serif; font-size:0.78rem;
                            color:#A9B1A6; line-height:1.7;">
                    <div style="font-weight:600; color:#F7F5F2;">Shaik Irfan</div>
                    <div>TBC CSE AI & DE</div>
                    <div>Data Engineering - Week 2</div>
                    <div style="margin-top:0.5rem; font-size:0.7rem; color:#6B7566;">
                        Last Updated: <span style="font-family:'Space Grotesk',sans-serif;">{last_run}</span>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
