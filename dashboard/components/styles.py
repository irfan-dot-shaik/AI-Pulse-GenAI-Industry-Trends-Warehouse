# =============================================================================
# dashboard/components/styles.py — AI Pulse Dashboard
# =============================================================================
#
# DESIGN LANGUAGE: Old Money · Quiet Luxury · Executive Dashboard
#
# Inspired by: Bloomberg Terminal, Stripe Dashboard, Linear.app,
#              Porsche/Bentley/Rolex brand language, Apple UI Philosophy.
#
# PALETTE:
#   Background:        #0F1512  — Deep forest, near-black
#   Secondary BG:      #17201B  — Slightly lighter forest
#   Card BG:           #1C2721  — Elevated card surface
#   Primary Gold:      #C8A96A  — Warm antique gold (never neon)
#   Secondary Gold:    #D8C18B  — Lighter gold for hover/secondary
#   Success Green:     #6E9F67  — Muted forest green
#   Warning:           #C9984A  — Warm amber
#   Danger:            #B35C4A  — Muted terracotta
#   Text:              #F7F5F2  — Warm near-white (not cold white)
#   Muted Text:        #A9B1A6  — Warm gray
#   Border:            rgba(200,169,106,0.10) — whisper-thin gold
#
# TYPOGRAPHY:
#   Headings:  Cormorant Garamond — editorial, old money serif
#   Body:      Inter — clean, readable sans-serif
#   Numbers:   Space Grotesk — precise, financial feel
#
# =============================================================================

import streamlit as st

_CSS = """
<style>
/* ============================================================
   GOOGLE FONTS — Premium Typography
   ============================================================ */
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,500;0,600;0,700;1,400;1,600&family=Inter:wght@300;400;500;600;700&family=Space+Grotesk:wght@400;500;600;700&family=Manrope:wght@300;400;500;600;700&display=swap');

/* ============================================================
   CSS DESIGN TOKENS — Single source of truth
   ============================================================ */
:root {
    /* Backgrounds */
    --bg:           #0D120F; /* Slightly deeper luxury forest */
    --bg-2:         #151C18;
    --bg-card:      #19221D;
    --bg-card-hover:#1E2923;
    --bg-input:     #171F1A;

    /* Brand */
    --gold:         #C8A96A;
    --gold-light:   #D8C18B;
    --gold-dim:     rgba(200,169,106,0.15);
    --gold-border:  rgba(200,169,106,0.12);
    --gold-glow:    rgba(200,169,106,0.08);

    /* Semantic */
    --success:      #6E9F67;
    --warning:      #C9984A;
    --danger:       #B35C4A;
    --info:         #5E8FAA;

    /* Text */
    --text:         #F7F5F2;
    --text-muted:   #A9B1A6;
    --text-dim:     #6B7566;

    /* Borders */
    --border:       rgba(200,169,106,0.10);
    --border-strong:rgba(200,169,106,0.22);
    --border-card:  rgba(200,169,106,0.08);

    /* Typography */
    --font-serif:   'Cormorant Garamond', Georgia, serif;
    --font-body:    'Inter', 'Manrope', system-ui, sans-serif;
    --font-num:     'Space Grotesk', 'Inter', sans-serif;

    /* Spacing */
    --radius:       12px;
    --radius-sm:    8px;
    --radius-lg:    16px;
    --radius-pill:  999px;

    /* Shadows */
    --shadow-sm:    0 2px 4px rgba(0,0,0,0.25), 0 1px 2px rgba(0,0,0,0.15);
    --shadow-card:  0 6px 24px rgba(0,0,0,0.4), 0 0 0 1px var(--border-card);
    --shadow-hover: 0 12px 40px rgba(0,0,0,0.5), 0 0 0 1px var(--border-strong);
    --shadow-gold:  0 0 30px rgba(200,169,106,0.08);

    /* Animation */
    --ease:         cubic-bezier(0.2, 0.0, 0, 1.0);
    --dur:          300ms;
}

/* ============================================================
   BASE
   ============================================================ */
html, body, [class*="css"] {
    font-family: var(--font-body) !important;
    color: var(--text) !important;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
}

.stApp {
    background-color: var(--bg) !important;
}

/* ============================================================
   SIDEBAR
   ============================================================ */
section[data-testid="stSidebar"] {
    background-color: var(--bg-2) !important;
    border-right: 1px solid var(--border) !important;
}

section[data-testid="stSidebar"] > div {
    padding-top: 0 !important;
}

/* ============================================================
   TYPOGRAPHY — Hierarchy
   ============================================================ */
h1, h1 * {
    font-family: var(--font-serif) !important;
    font-size: 2.6rem !important;
    font-weight: 600 !important;
    letter-spacing: -0.01em;
    color: var(--text) !important;
    line-height: 1.2 !important;
    -webkit-text-fill-color: var(--text) !important;
    background: none !important;
}

h2, h2 * {
    font-family: var(--font-serif) !important;
    font-size: 1.65rem !important;
    font-weight: 600 !important;
    color: var(--text) !important;
    letter-spacing: -0.005em;
    margin-top: 2rem !important;
    margin-bottom: 0.6rem !important;
}

h3, h3 * {
    font-family: var(--font-body) !important;
    font-size: 0.72rem !important;
    font-weight: 700 !important;
    color: var(--text-muted) !important;
    letter-spacing: 0.1em;
    text-transform: uppercase !important;
}

/* Paragraph / body text */
p, li, div[class*="stMarkdown"] p {
    font-family: var(--font-body) !important;
    color: var(--text-muted) !important;
    line-height: 1.7;
}

/* ============================================================
   KPI METRIC CARDS
   ============================================================ */
div[data-testid="metric-container"] {
    background: var(--bg-card) !important;
    border: 1px solid var(--border-card) !important;
    border-radius: var(--radius-lg) !important;
    padding: 1.8rem 1.8rem 1.6rem !important;
    box-shadow: var(--shadow-card) !important;
    transition: transform var(--dur) var(--ease),
                box-shadow var(--dur) var(--ease),
                border-color var(--dur) var(--ease) !important;
    position: relative;
    overflow: hidden;
}

div[data-testid="metric-container"]::after {
    content: '';
    position: absolute;
    bottom: 0; left: 0; right: 0;
    height: 2px;
    background: linear-gradient(90deg, var(--gold) 0%, transparent 100%);
    opacity: 0.6;
    border-radius: 0 0 var(--radius-lg) var(--radius-lg);
}

div[data-testid="metric-container"]:hover {
    transform: translateY(-3px) !important;
    box-shadow: var(--shadow-hover) !important;
    border-color: var(--border-strong) !important;
}

div[data-testid="metric-container"] label,
div[data-testid="metric-container"] [data-testid="stMetricLabel"] {
    font-family: var(--font-body) !important;
    font-size: 0.68rem !important;
    font-weight: 700 !important;
    letter-spacing: 0.12em !important;
    text-transform: uppercase !important;
    color: var(--text-muted) !important;
}

div[data-testid="metric-container"] [data-testid="stMetricValue"] > div {
    font-family: var(--font-num) !important;
    font-size: 2.3rem !important;
    font-weight: 500 !important;
    color: var(--text) !important;
    letter-spacing: -0.03em;
    line-height: 1.2;
}

div[data-testid="metric-container"] [data-testid="stMetricDelta"] {
    font-family: var(--font-body) !important;
    font-size: 0.72rem !important;
    color: var(--text-dim) !important;
    margin-top: 0.2rem;
}

/* ============================================================
   ARTICLE CARDS
   ============================================================ */
.article-card {
    background: var(--bg-card);
    border: 1px solid var(--border-card);
    border-radius: var(--radius-lg);
    padding: 1.8rem 2rem;
    margin-bottom: 1rem;
    box-shadow: var(--shadow-card);
    transition: transform var(--dur) var(--ease),
                box-shadow var(--dur) var(--ease),
                border-color var(--dur) var(--ease);
    position: relative;
    overflow: hidden;
}

.article-card::before {
    content: '';
    position: absolute;
    left: 0; top: 0; bottom: 0;
    width: 3px;
    background: var(--gold);
    opacity: 0;
    border-radius: var(--radius-lg) 0 0 var(--radius-lg);
    transition: opacity var(--dur) var(--ease);
}

.article-card:hover {
    transform: translateY(-2px);
    box-shadow: var(--shadow-hover);
    border-color: var(--border-strong);
}

.article-card:hover::before {
    opacity: 0.7;
}

.article-title a {
    font-family: var(--font-serif) !important;
    font-size: 1.2rem;
    font-weight: 600;
    color: var(--text) !important;
    text-decoration: none;
    line-height: 1.4;
    display: block;
    transition: color var(--dur) var(--ease);
}

.article-title a:hover {
    color: var(--gold-light) !important;
}

.article-meta {
    font-size: 0.78rem;
    color: var(--text-dim);
    margin: 0.6rem 0 0.8rem;
    display: flex;
    align-items: center;
    gap: 0.4rem;
}

.article-description {
    font-size: 0.86rem;
    color: var(--text-muted);
    line-height: 1.65;
    margin-bottom: 0.65rem;
}

/* ============================================================
   SCORE BADGES
   ============================================================ */
.badge {
    display: inline-flex;
    align-items: center;
    gap: 0.25rem;
    padding: 0.22rem 0.7rem;
    border-radius: var(--radius-pill);
    font-family: var(--font-body);
    font-size: 0.68rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.07em;
    white-space: nowrap;
}

/* Gold — Hot Trend */
.badge-hot {
    background: rgba(200,169,106,0.12);
    color: #D8C18B;
    border: 1px solid rgba(200,169,106,0.25);
}

/* Warm amber — High Impact */
.badge-high {
    background: rgba(201,152,74,0.12);
    color: #D4A96B;
    border: 1px solid rgba(201,152,74,0.25);
}

/* Forest green — Trending */
.badge-trend {
    background: rgba(110,159,103,0.12);
    color: #8BBD85;
    border: 1px solid rgba(110,159,103,0.25);
}

/* Stone — Normal */
.badge-normal {
    background: rgba(169,177,166,0.08);
    color: #A9B1A6;
    border: 1px solid rgba(169,177,166,0.15);
}

/* ============================================================
   KEYWORD TAGS
   ============================================================ */
.kw-tag {
    display: inline-block;
    padding: 0.16rem 0.5rem;
    border-radius: var(--radius-sm);
    font-family: var(--font-body);
    font-size: 0.68rem;
    font-weight: 500;
    background: rgba(200,169,106,0.07);
    color: var(--gold-light);
    border: 1px solid rgba(200,169,106,0.14);
    margin: 0.1rem 0.12rem;
    letter-spacing: 0.02em;
}

/* ============================================================
   STATUS DOTS
   ============================================================ */
.status-dot {
    display: inline-block;
    width: 8px; height: 8px;
    border-radius: 50%;
    flex-shrink: 0;
}

.status-dot.online {
    background: var(--success);
    box-shadow: 0 0 0 2px rgba(110,159,103,0.25);
}

.status-dot.offline {
    background: var(--danger);
    box-shadow: 0 0 0 2px rgba(179,92,74,0.25);
}

/* ============================================================
   HEALTH CARD (sidebar)
   ============================================================ */
.health-card {
    background: rgba(15,21,18,0.6);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 0;
    overflow: hidden;
}

.health-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 0.78rem;
    padding: 0.55rem 0.9rem;
    border-bottom: 1px solid var(--border);
    transition: background var(--dur) var(--ease);
}

.health-row:last-child { border-bottom: none; }

.health-row:hover { background: var(--bg-card-hover); }

.health-row .label { color: var(--text-muted); }
.health-row .value {
    font-family: var(--font-num);
    color: var(--text);
    font-weight: 600;
    font-size: 0.8rem;
}

/* ============================================================
   SECTION DIVIDERS
   ============================================================ */
.section-header {
    display: flex;
    align-items: center;
    gap: 1rem;
    margin: 3rem 0 1.5rem;
}

.section-label {
    font-family: var(--font-body);
    font-size: 0.68rem;
    font-weight: 700;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: var(--text-muted);
}

.section-line {
    flex: 1;
    height: 1px;
    background: var(--border);
}

.section-accent {
    width: 20px; height: 1px;
    background: var(--gold);
    opacity: 0.5;
}

/* ============================================================
   SEARCH / FILTER INPUTS
   ============================================================ */
div[data-baseweb="input"] input,
div[data-baseweb="textarea"] textarea {
    background: var(--bg-input) !important;
    border-color: var(--border) !important;
    color: var(--text) !important;
    font-family: var(--font-body) !important;
    border-radius: var(--radius-sm) !important;
    font-size: 0.88rem !important;
}

div[data-baseweb="input"] input:focus,
div[data-baseweb="textarea"] textarea:focus {
    border-color: var(--gold) !important;
    box-shadow: 0 0 0 2px rgba(200,169,106,0.15) !important;
}

div[data-baseweb="select"] > div {
    background: var(--bg-input) !important;
    border-color: var(--border) !important;
    border-radius: var(--radius-sm) !important;
}

/* ============================================================
   BUTTONS
   ============================================================ */
.stButton > button {
    background: transparent !important;
    color: var(--gold) !important;
    border: 1px solid var(--border-strong) !important;
    border-radius: var(--radius-sm) !important;
    font-family: var(--font-body) !important;
    font-size: 0.82rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.04em !important;
    padding: 0.5rem 1.2rem !important;
    transition: all var(--dur) var(--ease) !important;
}

.stButton > button:hover {
    background: var(--gold-dim) !important;
    border-color: var(--gold) !important;
    color: var(--gold-light) !important;
}

/* Primary button variant */
.stButton > button[kind="primary"] {
    background: var(--gold-dim) !important;
    border-color: var(--gold) !important;
    color: var(--gold-light) !important;
}

/* ============================================================
   TABS
   ============================================================ */
button[data-baseweb="tab"] {
    font-family: var(--font-body) !important;
    font-size: 0.82rem !important;
    font-weight: 600 !important;
    color: var(--text-muted) !important;
    letter-spacing: 0.04em !important;
}

button[data-baseweb="tab"][aria-selected="true"] {
    color: var(--gold) !important;
    border-bottom-color: var(--gold) !important;
}

/* ============================================================
   DATAFRAME / TABLE
   ============================================================ */
.stDataFrame {
    border-radius: var(--radius) !important;
    border: 1px solid var(--border) !important;
    overflow: hidden;
}

/* ============================================================
   SCROLLBARS
   ============================================================ */
::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: var(--bg); }
::-webkit-scrollbar-thumb {
    background: rgba(200,169,106,0.25);
    border-radius: 3px;
}
::-webkit-scrollbar-thumb:hover { background: rgba(200,169,106,0.45); }

/* ============================================================
   PLOTLY CHART CONTAINER
   ============================================================ */
.js-plotly-plot {
    border-radius: var(--radius) !important;
}

/* ============================================================
   PAGINATION BUTTONS
   ============================================================ */
.page-btn {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 34px; height: 34px;
    border-radius: var(--radius-sm);
    border: 1px solid var(--border);
    background: var(--bg-card);
    color: var(--text-muted);
    font-family: var(--font-num);
    font-size: 0.82rem;
    font-weight: 600;
    cursor: pointer;
    transition: all var(--dur) var(--ease);
}

.page-btn.active {
    background: var(--gold-dim);
    border-color: var(--gold);
    color: var(--gold-light);
}

/* ============================================================
   FILTER PANEL
   ============================================================ */
.filter-panel {
    background: var(--bg-2);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 1.2rem 1.4rem;
    margin-bottom: 1.4rem;
}

/* ============================================================
   EMPTY STATE
   ============================================================ */
.empty-state {
    text-align: center;
    padding: 4rem 2rem;
    color: var(--text-muted);
}

.empty-state-icon {
    font-size: 3rem;
    opacity: 0.3;
    display: block;
    margin-bottom: 1rem;
}

.empty-state-title {
    font-family: var(--font-serif);
    font-size: 1.4rem;
    font-weight: 600;
    color: var(--text-muted);
    margin-bottom: 0.4rem;
}

.empty-state-sub {
    font-size: 0.86rem;
    color: var(--text-dim);
}

/* ============================================================
   HIDE STREAMLIT CHROME
   ============================================================ */
#MainMenu { visibility: hidden; }
footer    { visibility: hidden; }
header[data-testid="stHeader"] { background: transparent; border-bottom: 1px solid var(--border); }

/* ============================================================
   STREAMLIT ALERTS — match theme
   ============================================================ */
div[data-testid="stAlert"] {
    border-radius: var(--radius) !important;
    border-left-width: 3px !important;
}

/* ============================================================
   SELECTBOX LABEL
   ============================================================ */
label[data-testid="stWidgetLabel"] {
    font-family: var(--font-body) !important;
    font-size: 0.72rem !important;
    font-weight: 700 !important;
    letter-spacing: 0.08em !important;
    text-transform: uppercase !important;
    color: var(--text-muted) !important;
}

/* ============================================================
   NUMBER INPUT
   ============================================================ */
input[type="number"] {
    background: var(--bg-input) !important;
    border-color: var(--border) !important;
    color: var(--text) !important;
    font-family: var(--font-num) !important;
}

/* Slider */
div[data-testid="stSlider"] [data-baseweb="slider"] [data-testid="stTickBar"] {
    color: var(--text-muted) !important;
    font-size: 0.72rem !important;
}
</style>
"""


def inject_styles() -> None:
    """
    Inject the complete AI Pulse CSS design system into the current page.
    Call this at the top of every page file, before any st.* rendering calls.
    """
    st.markdown(_CSS, unsafe_allow_html=True)


def render_page_header(title: str, subtitle: str, icon: str = "") -> None:
    """
    Render an elegant serif page header with muted subtitle.
    Uses Cormorant Garamond for the premium editorial feel.
    """
    st.markdown(
        f"""
        <div style="padding: 2rem 0 1.2rem 0; border-bottom: 1px solid var(--border); margin-bottom: 1.8rem;">
            <div style="font-family: var(--font-serif); font-size: 2.4rem; font-weight: 600;
                        color: var(--text); letter-spacing: -0.01em; line-height: 1.15;
                        margin-bottom: 0.4rem;">
                {title}
            </div>
            <div style="font-family: var(--font-body); font-size: 0.88rem; color: var(--text-muted);
                        line-height: 1.6; max-width: 680px;">
                {subtitle}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_section_header(label: str) -> None:
    """
    Render a minimal uppercase section divider — no emojis, pure typographic hierarchy.
    """
    st.markdown(
        f"""
        <div class="section-header">
            <span class="section-accent"></span>
            <span class="section-label">{label}</span>
            <div class="section-line"></div>
        </div>
        """,
        unsafe_allow_html=True,
    )
