# =============================================================================
# dashboard/components/footer.py — AI Pulse Dashboard
# =============================================================================
# Shared production footer rendered at the bottom of every page.
# =============================================================================

import streamlit as st
from datetime import datetime, timezone


def render_footer() -> None:
    """Render a professional production footer at the bottom of every page."""
    year = datetime.now(timezone.utc).year
    st.markdown(
        f"""
        <div style="margin-top:4rem; padding:1.8rem 0 1.2rem;
                    border-top:1px solid rgba(200,169,106,0.10);">
            <div style="display:flex; justify-content:space-between; align-items:flex-start;
                        max-width:100%; flex-wrap:wrap; gap:2rem;">
                <div>
                    <div style="font-family:'Cormorant Garamond',Georgia,serif;
                                font-size:1.15rem; font-weight:600; color:#F7F5F2;
                                margin-bottom:0.3rem;">
                        AI Pulse
                    </div>
                    <div style="font-family:'Inter',sans-serif; font-size:0.72rem;
                                color:#6B7566; line-height:1.7;">
                        GenAI Industry Trends Warehouse
                    </div>
                </div>
                <div style="font-family:'Inter',sans-serif; font-size:0.70rem;
                            color:#6B7566; line-height:1.9; text-align:center;">
                    <span style="color:#A9B1A6; font-weight:600;">Built by</span>
                    &nbsp;Shaik Irfan<br>
                    B.Tech CSE-AIDE · Foundations of Data Engineering
                </div>
                <div style="font-family:'Inter',sans-serif; font-size:0.70rem;
                            color:#6B7566; line-height:1.9; text-align:right;">
                    <span style="color:#A9B1A6;">Stack</span>
                    &nbsp;Python · PostgreSQL · Streamlit · Plotly<br>
                    <span style="color:#A9B1A6;">Version</span>
                    &nbsp;2.0 · Week 2
                </div>
            </div>
            <div style="margin-top:1rem; padding-top:0.8rem;
                        border-top:1px solid rgba(200,169,106,0.06);
                        font-family:'Inter',sans-serif; font-size:0.64rem;
                        color:#5C6359; text-align:center; letter-spacing:0.02em;">
                © {year} AI Pulse · Data Engineering Internship Project ·
                github.com/irfan-dot-shaik/AI-Pulse-GenAI-Industry-Trends-Warehouse
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
