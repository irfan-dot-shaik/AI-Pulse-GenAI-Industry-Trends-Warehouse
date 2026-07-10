# =============================================================================
# config/settings.py — AI Pulse Project
# =============================================================================
#
# PURPOSE:
#   This is the single source of truth for ALL configuration in the project.
#   Every setting, API parameter, and database URL lives here.
#   No other file should read from os.environ directly.
#
# CONCEPT — Why Centralize Config?
#   Imagine having 10 Python files, each reading environment variables.
#   If you rename a variable, you'd need to update 10 files.
#   By centralizing config here, you only change one file.
#   This is called the "Single Source of Truth" principle.
#
# CONCEPT — Why Not Hardcode Values?
#   BAD  (hardcoded):  API_KEY = "abc123xyz"
#   GOOD (from env):   API_KEY = os.getenv("GNEWS_API_KEY")
#
#   Hardcoding secrets means they go into Git history forever.
#   Even if you delete the line later, it still exists in commit history.
#
# FLOW:
#   .env file → python-dotenv loads it → os.environ → this file reads it
#
# =============================================================================

import os                          # Built-in Python module: access environment variables
from dotenv import load_dotenv     # Third-party: reads .env file into os.environ
from pathlib import Path           # Built-in: object-oriented way to handle file paths

# ---------------------------------------------------------------------------
# Load Environment Variables
# ---------------------------------------------------------------------------
# load_dotenv() searches for a .env file starting from the current directory
# and moving up the directory tree. It loads key=value pairs into os.environ.
#
# Path(__file__): absolute path to THIS file (settings.py)
# .parent:        the config/ folder
# .parent:        the project root folder (AI.NEWS/)
# / ".env":       the .env file in the project root
#
# We use dotenv_path to explicitly tell load_dotenv where to find .env,
# making the code work regardless of which directory you run it from.
# ---------------------------------------------------------------------------

# Get the absolute path of the project root directory
PROJECT_ROOT = Path(__file__).parent.parent

# Load the .env file from the project root
load_dotenv(dotenv_path=PROJECT_ROOT / ".env")


# =============================================================================
# GNews API Configuration
# =============================================================================
# GNews is the data source for this pipeline.
# All API-related settings are grouped together here.
# =============================================================================

# Your GNews API key — get it free at https://gnews.io
# os.getenv("KEY") returns None if the variable is not set.
# os.getenv("KEY", "default") returns "default" if not set.
GNEWS_API_KEY: str = os.getenv("GNEWS_API_KEY", "")

# The base URL for all GNews API requests
GNEWS_BASE_URL: str = "https://gnews.io/api/v4/search"

# The search query — what topics to search for in news articles
GNEWS_QUERY: str = os.getenv(
    "GNEWS_QUERY",
    "artificial intelligence OR generative AI OR OpenAI OR Google Gemini OR Anthropic"
)

# Maximum number of articles to fetch per API call
# Free tier limit: 10 articles per request
GNEWS_MAX_RESULTS: int = int(os.getenv("GNEWS_MAX_RESULTS", "10"))

# Language filter: "en" = English articles only
GNEWS_LANGUAGE: str = os.getenv("GNEWS_LANGUAGE", "en")

# Country filter: "us" = news from United States sources
GNEWS_COUNTRY: str = os.getenv("GNEWS_COUNTRY", "us")

# Category tag applied to ALL articles fetched by this pipeline
# Useful for filtering when you add more categories later (Week 3)
GNEWS_CATEGORY: str = "AI"


# =============================================================================
# Database Configuration
# =============================================================================
# SQLAlchemy uses a "connection URL" to know which database to connect to.
# The format is: dialect+driver://username:password@host:port/database
#
# Examples:
#   postgresql://postgres:postgres@localhost:5432/ai_pulse_db  → PostgreSQL
#   sqlite:///local.db                                          → SQLite (file-based)
# =============================================================================

# Full database connection URL — read from .env file
DATABASE_URL: str = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/ai_pulse_db"
)

# Name of the raw data table in PostgreSQL
# "raw_" prefix is a Data Engineering convention:
#   raw_  → data exactly as it came from the source (no transformations)
#   stg_  → staging: lightly cleaned
#   fct_  → fact tables: cleaned and modeled (Week 2+)
RAW_TABLE_NAME: str = "raw_ai_news"


# =============================================================================
# Logging Configuration
# =============================================================================

# Log level controls how much information is printed/saved
# DEBUG   → everything (very verbose, for development)
# INFO    → normal operations (what we use here)
# WARNING → something unexpected but non-fatal
# ERROR   → something went wrong
# CRITICAL → system cannot continue
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

# Path to the log file — stored in the logs/ folder at project root
LOG_FILE_PATH: Path = PROJECT_ROOT / "logs" / "pipeline.log"


# =============================================================================
# Validation
# =============================================================================
# This function checks that required settings are present.
# A Senior DE always validates configuration at startup — fail fast and loudly.
# =============================================================================

def validate_config() -> None:
    """
    Validate that all required environment variables are set.

    Raises:
        ValueError: If a required environment variable is missing.

    CONCEPT — Fail Fast:
        If your API key is missing, it's better to crash immediately with a
        clear error message than to run for 10 minutes and fail mysteriously.
        This is called "failing fast" — a core software engineering principle.
    """
    # List of variables that must not be empty
    required_vars = {
        "GNEWS_API_KEY": GNEWS_API_KEY,
        "DATABASE_URL": DATABASE_URL,
    }

    # Check each required variable
    missing = [name for name, value in required_vars.items() if not value]

    if missing:
        raise ValueError(
            f"Missing required environment variables: {', '.join(missing)}\n"
            f"Please check your .env file. See .env.example for reference."
        )


# =============================================================================
# Week 2 — Staging & Processing Configuration
# =============================================================================
# These constants are NEW in Week 2.
# All Week 1 settings above are completely untouched.
# =============================================================================

# Name of the staging table in PostgreSQL
# "stg_" prefix = staging layer (cleaned, validated, scored)
STG_TABLE_NAME: str = "stg_ai_news"

# Minimum description length (chars) to be considered for higher content scores
# Articles shorter than this get the lowest content length score
PROCESSING_MIN_DESC_LENGTH: int = 50

# Maximum description length stored in staging (longer text is truncated)
# This prevents extremely long articles from bloating the DB
PROCESSING_MAX_DESC_LENGTH: int = 1000

# Minimum title length (chars) — shorter titles fail validation
PROCESSING_MIN_TITLE_LENGTH: int = 10


# =============================================================================
# Week 3 — Multi-Source Ingestion Configuration
# =============================================================================
# These constants are NEW in Week 3.
# All Week 1 and 2 settings above are completely untouched.
# =============================================================================

# -----------------------------------------------------------------------------
# Reddit API (via PRAW — Python Reddit API Wrapper)
# -----------------------------------------------------------------------------
# How to get credentials (free):
#   1. Go to https://www.reddit.com/prefs/apps
#   2. Click "Create App" → type: "script"
#   3. Copy the client_id (under the app name) and client_secret
#   4. Use any user-agent string describing your bot
#
# These are OPTIONAL. If not set, Reddit ingestion is silently skipped.
# GNews and Hacker News will still run.
# -----------------------------------------------------------------------------

REDDIT_CLIENT_ID: str = os.getenv("REDDIT_CLIENT_ID", "")
REDDIT_CLIENT_SECRET: str = os.getenv("REDDIT_CLIENT_SECRET", "")
REDDIT_USER_AGENT: str = os.getenv("REDDIT_USER_AGENT", "ai_pulse_bot/1.0 by AI_Pulse_Project")

# Subreddits to scrape — comma-separated string in .env, split here
_reddit_subs_raw: str = os.getenv(
    "REDDIT_SUBREDDITS",
    "MachineLearning,artificial,singularity"
)
REDDIT_SUBREDDITS: list[str] = [s.strip() for s in _reddit_subs_raw.split(",") if s.strip()]

# Number of hot/new posts to fetch per subreddit
REDDIT_POST_LIMIT: int = int(os.getenv("REDDIT_POST_LIMIT", "10"))

# -----------------------------------------------------------------------------
# Hacker News API (Firebase REST — no authentication required)
# -----------------------------------------------------------------------------
# The HN Firebase API is completely free, public, and unlimited.
# Docs: https://github.com/HackerNews/API
#
# We query three feeds and merge unique IDs to maximise coverage:
#   topstories  → what HN users are upvoting most right now
#   beststories → the all-time best-rated stories (higher quality signal)
#   newstories  → the very latest submissions (freshness signal)
# -----------------------------------------------------------------------------

HN_BASE_URL: str = "https://hacker-news.firebaseio.com/v0"

# Number of top stories to inspect for AI relevance (from the merged ID pool)
# We fetch 3 lists (top/best/new) and inspect the first HN_INSPECT_LIMIT unique IDs.
# A higher limit = more AI articles found, but more HTTP calls.
HN_INSPECT_LIMIT: int = int(os.getenv("HN_INSPECT_LIMIT", "100"))

# Final number of AI-relevant HN articles to return per run
HN_FETCH_LIMIT: int = int(os.getenv("HN_FETCH_LIMIT", "10"))
