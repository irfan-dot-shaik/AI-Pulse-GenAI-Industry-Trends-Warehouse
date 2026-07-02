# =============================================================================
# processing/transformer.py — AI Pulse Project
# =============================================================================
#
# PURPOSE:
#   Transforms validated raw articles into clean, normalized records ready
#   for the staging layer (stg_ai_news table).
#
# CONCEPT — Why Transform Data?
#   Raw API data often contains:
#     - Extra whitespace: "  TechCrunch  " → "TechCrunch"
#     - Mixed capitalization: "techcrunch" → "TechCrunch"
#     - Inconsistent author strings: "" → "Unknown"
#     - Oversized text: descriptions truncated at DB safe length
#
#   The staging layer (stg_ai_news) should contain clean, consistent data.
#   The raw layer (raw_ai_news) always keeps the original as-is.
#
# CONCEPT — Raw vs. Staging Layer:
#   RAW    → data as-is from the source (never modified)
#   STAGING → cleaned version of raw (what analytics queries run against)
#
#   If you discover a bug in your cleaning logic, you can always re-derive
#   the staging layer from the raw layer. This is why we keep both.
#
# TRANSFORMATIONS APPLIED:
#   1. Strip leading/trailing whitespace from all text fields
#   2. Title-case source names:  "techcrunch" → "TechCrunch"
#   3. Normalize author:         "", None, "Unknown" → "Unknown"
#   4. Truncate description to 1000 chars (safety limit for display)
#   5. Uppercase category:       "ai" → "AI"
#   6. Add is_valid=True column  (all rows here passed validation)
#   7. Add validation_notes=""   (empty = no issues found)
#
# =============================================================================

import pandas as pd                   # DataFrame manipulation
from utils.logger import get_logger   # Our centralized logger

logger = get_logger(__name__)

# Maximum characters to keep in description field
# Longer descriptions are truncated — they don't add analytical value
MAX_DESCRIPTION_LENGTH: int = 1000


# =============================================================================
# Individual Transformation Functions
# =============================================================================
# Each transformation is a pure function: same input always gives same output.
# No side effects, no logging inside — clean and testable.
# =============================================================================

def _clean_text(value: str, default: str = "") -> str:
    """
    Strip whitespace from a string value.

    Args:
        value:   The string to clean. Can be None.
        default: Value to return if value is None or empty after stripping.

    Returns:
        str: Cleaned string, or default if empty.
    """
    if value is None:
        return default
    cleaned = str(value).strip()
    return cleaned if cleaned else default


def _normalize_source(source: str) -> str:
    """
    Normalize source name: strip whitespace and apply title-case.

    Examples:
        "techcrunch"    → "Techcrunch"   (title-case)
        "  WIRED  "     → "Wired"         (strip + title-case)
        ""              → "Unknown Source"
        None            → "Unknown Source"

    Args:
        source: Raw source name from API.

    Returns:
        str: Normalized source name.
    """
    if not source:
        return "Unknown Source"
    cleaned = source.strip()
    if not cleaned:
        return "Unknown Source"
    # Title-case: first letter of each word capitalized
    return cleaned.title()


def _normalize_author(author: str) -> str:
    """
    Normalize author field.

    GNews rarely provides an author. We standardize all empty/unknown
    values to "Unknown" for consistent filtering in the dashboard.

    Args:
        author: Raw author string from API (often empty or "Unknown").

    Returns:
        str: Normalized author name, or "Unknown".
    """
    if not author:
        return "Unknown"
    cleaned = author.strip()
    if not cleaned or cleaned.lower() in ("unknown", "n/a", "none"):
        return "Unknown"
    return cleaned


def _truncate(text: str, max_length: int = MAX_DESCRIPTION_LENGTH) -> str:
    """
    Truncate text to max_length characters.

    Adds "..." at the end if truncated so readers know there's more.

    Args:
        text:       String to potentially truncate.
        max_length: Maximum allowed length (default 1000).

    Returns:
        str: Original or truncated string.
    """
    if not text:
        return ""
    text = str(text).strip()
    if len(text) <= max_length:
        return text
    return text[:max_length - 3] + "..."


def _normalize_category(category: str) -> str:
    """
    Normalize category to uppercase.

    Args:
        category: Category string (e.g., "ai", "Ai", "AI").

    Returns:
        str: Uppercase category, or "AI" if empty.
    """
    if not category:
        return "AI"
    return str(category).strip().upper()


# =============================================================================
# Main Transformation Function
# =============================================================================

def transform_articles(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply all transformations to a validated DataFrame of articles.

    Takes the output of validate_articles().valid_df and returns a clean
    DataFrame ready to be scored (scorer.py) and then loaded to stg_ai_news.

    Transformations applied (in order):
        1. Strip whitespace from title, description, url, author, source
        2. Normalize source names (title-case)
        3. Normalize author field (standardize unknowns)
        4. Truncate description to MAX_DESCRIPTION_LENGTH
        5. Normalize category to uppercase
        6. Add is_valid=True (these rows passed validator.py)
        7. Add validation_notes="" (no issues for valid rows)

    Args:
        df (pd.DataFrame): Valid articles from validate_articles().valid_df.
                           Must have columns: title, source, author, description,
                           published_at, url, category.

    Returns:
        pd.DataFrame: Transformed DataFrame with clean values + 2 new columns.
                      This is the DataFrame passed to score_articles().

    CONCEPT — Non-destructive:
        We work on a copy of the input DataFrame.
        The original DataFrame (from validate_articles) is unchanged.
        This is called "immutable data flow" — a best practice in Data Engineering.
    """
    if df is None or df.empty:
        logger.warning("transform_articles() received empty DataFrame.")
        return df

    logger.info(f"Transforming {len(df)} validated articles...")

    # Always work on a copy — never modify the input
    clean_df = df.copy()

    # -------------------------------------------------------------------------
    # Transformation 1: Clean title
    # "  OpenAI releases GPT-5  " → "OpenAI releases GPT-5"
    # -------------------------------------------------------------------------
    clean_df["title"] = clean_df["title"].apply(
        lambda x: _clean_text(x, default="No Title")
    )

    # -------------------------------------------------------------------------
    # Transformation 2: Normalize source
    # "techcrunch" → "Techcrunch", None → "Unknown Source"
    # -------------------------------------------------------------------------
    clean_df["source"] = clean_df["source"].apply(_normalize_source)

    # -------------------------------------------------------------------------
    # Transformation 3: Normalize author
    # "", None, "unknown" → "Unknown"
    # -------------------------------------------------------------------------
    clean_df["author"] = clean_df["author"].apply(_normalize_author)

    # -------------------------------------------------------------------------
    # Transformation 4: Clean and truncate description
    # Long descriptions → truncated to 1000 chars + "..."
    # -------------------------------------------------------------------------
    clean_df["description"] = clean_df["description"].apply(
        lambda x: _truncate(_clean_text(x, default=""), MAX_DESCRIPTION_LENGTH)
    )

    # -------------------------------------------------------------------------
    # Transformation 5: Normalize URL (just strip whitespace)
    # URLs should not be modified further — they are our idempotency keys
    # -------------------------------------------------------------------------
    clean_df["url"] = clean_df["url"].apply(lambda x: _clean_text(x, default=""))

    # -------------------------------------------------------------------------
    # Transformation 6: Normalize category to uppercase
    # "ai" → "AI"
    # -------------------------------------------------------------------------
    clean_df["category"] = clean_df["category"].apply(_normalize_category)

    # -------------------------------------------------------------------------
    # Transformation 7: Add staging metadata columns
    # These columns exist on stg_ai_news but not raw_ai_news
    # -------------------------------------------------------------------------
    # is_valid=True: all rows here have passed validator.py
    clean_df["is_valid"]          = True
    # validation_notes="": no issues (blank = clean)
    clean_df["validation_notes"]  = ""

    logger.info(
        f"Transformation complete. "
        f"Columns: {list(clean_df.columns)}"
    )

    return clean_df
