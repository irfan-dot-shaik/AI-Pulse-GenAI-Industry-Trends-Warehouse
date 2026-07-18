# =============================================================================
# dashboard/utils/error_boundary.py — AI Pulse Dashboard
# =============================================================================
# Context manager for graceful error handling in Streamlit.
# Prevents Python tracebacks from leaking to users.
# =============================================================================

import streamlit as st
from contextlib import contextmanager
import logging

logger = logging.getLogger(__name__)

@contextmanager
def error_boundary(fallback_msg: str = "An unexpected error occurred while loading this section."):
    """
    Context manager that catches all exceptions and displays a graceful
    UI error message instead of a traceback.
    """
    try:
        yield
    except Exception as e:
        logger.error(f"UI Error: {e}", exc_info=True)
        st.markdown(
            f"""
            <div style="background:#1C2721; border:1px solid rgba(179,92,74,0.3);
                        border-radius:10px; padding:1.4rem; margin:1rem 0;
                        border-left:4px solid #B35C4A;">
                <div style="font-family:'Cormorant Garamond',serif; font-size:1.3rem;
                            font-weight:600; color:#F7F5F2; margin-bottom:0.4rem;">
                    Unable to Load Section
                </div>
                <div style="font-family:'Inter',sans-serif; font-size:0.86rem;
                            color:#A9B1A6; line-height:1.6;">
                    {fallback_msg}
                </div>
                <div style="font-family:'Inter',sans-serif; font-size:0.75rem;
                            color:#6B7566; margin-top:0.8rem; font-style:italic;">
                    Please check that PostgreSQL is running and the pipeline has been executed.
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
