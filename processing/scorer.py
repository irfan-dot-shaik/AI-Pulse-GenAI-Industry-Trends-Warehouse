# =============================================================================
# processing/scorer.py — AI Pulse Project
# =============================================================================
#
# PURPOSE:
#   Computes the AI News Intelligence Score (0–100) for each article.
#   This score represents how relevant, credible, timely, and detailed
#   an article is within the GenAI news space.
#
# CONCEPT — Rule-Based Scoring vs. Machine Learning:
#   A machine learning model requires labelled training data (thousands of
#   articles rated by humans) before it can predict scores. We don't have
#   that yet. A rule-based system is:
#     - Fully transparent: every point can be explained
#     - Immediately deployable: no training needed
#     - Auditable: your mentor can verify every score by hand
#     - Extendable: add new rules without retraining
#
#   This is a deliberate, correct engineering choice for Week 2.
#   (ML scoring is a great Week 4+ enhancement.)
#
# SCORING COMPONENTS (total = 100 points):
#
#   Component 1: RECENCY (max 30 pts)
#   ─────────────────────────────────
#   Published < 6 hours ago    →  30 pts  (Breaking news)
#   Published < 24 hours ago   →  25 pts  (Today's news)
#   Published < 3 days ago     →  20 pts  (Recent)
#   Published < 7 days ago     →  12 pts  (This week)
#   Published >= 7 days ago    →   5 pts  (Older)
#
#   Component 2: AI KEYWORD RELEVANCE (max 40 pts)
#   ──────────────────────────────────────────────
#   Searches both title and description for 20 AI keywords.
#   Score = min(matches * 5, 40) — each keyword worth 5 pts, capped at 40.
#
#   Component 3: SOURCE CREDIBILITY (max 20 pts)
#   ─────────────────────────────────────────────
#   Tier 1 (Reuters, Bloomberg, AP, WSJ, FT)          → 20 pts
#   Tier 2 (TechCrunch, Wired, MIT Tech, CNBC, Verge) → 15 pts
#   Tier 3 (Other known sources)                       →  8 pts
#   Unknown sources                                    →  3 pts
#
#   Component 4: CONTENT LENGTH (max 10 pts)
#   ─────────────────────────────────────────
#   description > 200 chars  → 10 pts  (Detailed article)
#   description > 100 chars  →  7 pts  (Moderate detail)
#   description > 50 chars   →  4 pts  (Brief)
#   description <= 50 chars  →  1 pt   (Very short/stub)
#
# SCORE CATEGORIES:
#   90 – 100 = "Hot Trend"    (Breaking, highly relevant, top source)
#   75 –  89 = "High Impact"  (Very relevant, credible source)
#   50 –  74 = "Trending"     (Relevant but older or less credible)
#   00 –  49 = "Normal"       (Low relevance, old, or stub article)
#
# =============================================================================

import pandas as pd                      # DataFrame manipulation
from datetime import datetime, timezone  # For recency calculation
from typing import Optional              # For nullable type hints
from utils.logger import get_logger      # Our centralized logger

logger = get_logger(__name__)


# =============================================================================
# Configuration Constants
# =============================================================================
# Keeping keywords and sources as constants (not magic strings inside functions)
# makes them easy to update and test independently.
# =============================================================================

# 20 AI-specific keywords to search for in title + description
# Each match contributes 5 points to the relevance score (capped at 40)
AI_KEYWORDS: list[str] = [
    "openai",
    "chatgpt",
    "gpt",
    "gemini",
    "claude",
    "anthropic",
    "nvidia",
    "microsoft ai",
    "google ai",
    "llm",
    "large language model",
    "generative ai",
    "artificial intelligence",
    "machine learning",
    "deep learning",
    "foundation model",
    "ai model",
    "transformer",
    "neural network",
    "copilot",
]

# Source credibility tiers
# Keys are lowercase source name substrings (partial match is fine)
TIER_1_SOURCES: list[str] = [
    "reuters",
    "bloomberg",
    "associated press",
    "ap news",
    "wall street journal",
    "financial times",
    "new york times",
    "washington post",
    "bbc",
    "the guardian",
]

TIER_2_SOURCES: list[str] = [
    "techcrunch",
    "wired",
    "mit technology review",
    "cnbc",
    "the verge",
    "ars technica",
    "venturebeat",
    "zdnet",
    "ieee spectrum",
    "fortune",
    "fast company",
    "business insider",
]

# Score category thresholds
CATEGORY_HOT_TREND:  tuple[int, int] = (90, 100)
CATEGORY_HIGH_IMPACT: tuple[int, int] = (75, 89)
CATEGORY_TRENDING:   tuple[int, int] = (50, 74)
CATEGORY_NORMAL:     tuple[int, int] = (0,  49)


# =============================================================================
# Individual Scoring Components
# =============================================================================

def _score_recency(published_at) -> int:
    """
    Score an article based on how recently it was published (max 30 pts).

    Args:
        published_at: datetime object (timezone-aware) or None.

    Returns:
        int: Recency score between 0 and 30.

    CONCEPT — Why Recency Matters:
        In AI news, a 7-day-old article about GPT-5 is old news.
        Recency rewards timely reporting, which is what executives want.
    """
    if published_at is None:
        return 5  # Default: assume older if timestamp missing

    # Normalize: ensure both datetimes are timezone-aware for comparison
    now = datetime.now(timezone.utc)

    # Handle both tz-aware and tz-naive published_at values
    try:
        if hasattr(published_at, 'tzinfo') and published_at.tzinfo is not None:
            delta = now - published_at
        else:
            # Treat as UTC if no timezone info
            delta = now - published_at.replace(tzinfo=timezone.utc)

        hours_old = delta.total_seconds() / 3600  # Convert seconds to hours

        if hours_old < 6:
            return 30   # Breaking news
        elif hours_old < 24:
            return 25   # Today's news
        elif hours_old < 72:   # 3 days
            return 20   # Recent
        elif hours_old < 168:  # 7 days
            return 12   # This week
        else:
            return 5    # Older

    except (TypeError, AttributeError, OverflowError):
        # If any datetime comparison fails, return a safe default
        logger.debug(f"Could not compute recency for published_at={published_at}")
        return 5


def _score_keyword_relevance(title: str, description: str) -> tuple[int, list[str]]:
    """
    Score an article based on how many AI keywords appear in its text (max 40 pts).

    Searches both title and description (combined) for each keyword.
    Case-insensitive matching.

    Args:
        title:       Article title string.
        description: Article description/summary string.

    Returns:
        tuple[int, list[str]]:
            - Score (0–40)
            - List of matched keyword strings (for display in dashboard)

    CONCEPT — Why Search Both Title and Description?
        The title alone may not contain all keywords.
        "OpenAI's New Model" might have "GPT" only in the description.
        Searching both gives a more complete picture.
    """
    # Combine title and description into one lowercase searchable string
    text = f"{title or ''} {description or ''}".lower()

    matched_keywords = []
    for keyword in AI_KEYWORDS:
        if keyword.lower() in text:
            matched_keywords.append(keyword)

    # Each keyword is worth 5 pts, maximum 40
    score = min(len(matched_keywords) * 5, 40)
    return score, matched_keywords


def _score_source_credibility(source: str) -> int:
    """
    Score an article based on the credibility tier of its source (max 20 pts).

    Args:
        source: Name of the news source (e.g., "TechCrunch", "Reuters").

    Returns:
        int: Credibility score (20, 15, 8, or 3).

    CONCEPT — Why Source Credibility?
        Not all news sources are equal. Reuters follows strict editorial
        standards; a random blog may not. Weighting sources encourages
        the system to surface credible news at the top.
    """
    if not source:
        return 3  # Unknown source gets minimum points

    source_lower = source.lower()

    # Check Tier 1 first (highest credibility)
    for tier1 in TIER_1_SOURCES:
        if tier1 in source_lower:
            return 20

    # Check Tier 2
    for tier2 in TIER_2_SOURCES:
        if tier2 in source_lower:
            return 15

    # Known but not tier 1 or 2 — still a legitimate source
    return 8


def _score_content_length(description: str) -> int:
    """
    Score an article based on the length of its description (max 10 pts).

    Args:
        description: Article description/summary string.

    Returns:
        int: Length score (10, 7, 4, or 1).

    CONCEPT — Why Content Length?
        Stub articles (< 50 chars) are low quality — often just a headline
        with no context. Detailed descriptions signal a full article worth reading.
    """
    if not description:
        return 1  # No description at all

    length = len(description.strip())

    if length > 200:
        return 10   # Detailed
    elif length > 100:
        return 7    # Moderate
    elif length > 50:
        return 4    # Brief
    else:
        return 1    # Very short


def _get_score_category(score: int) -> str:
    """
    Convert a numeric score (0–100) to a human-readable category label.

    Args:
        score: Integer score between 0 and 100.

    Returns:
        str: One of 'Hot Trend', 'High Impact', 'Trending', 'Normal'.
    """
    if score >= CATEGORY_HOT_TREND[0]:
        return "Hot Trend"
    elif score >= CATEGORY_HIGH_IMPACT[0]:
        return "High Impact"
    elif score >= CATEGORY_TRENDING[0]:
        return "Trending"
    else:
        return "Normal"


# =============================================================================
# Main Scoring Function
# =============================================================================

def compute_article_score(
    title: str,
    description: str,
    source: str,
    published_at
) -> tuple[int, str, str]:
    """
    Compute the AI News Intelligence Score for a single article.

    This function combines all four scoring components into a final score.
    Each component is independently calculated and logged for transparency.

    Args:
        title:        Article title.
        description:  Article description or summary.
        source:       Name of the news source.
        published_at: Publication datetime (timezone-aware preferred).

    Returns:
        tuple[int, str, str]:
            - score:          Final score (0–100)
            - category:       Score category label
            - keywords_found: Comma-separated string of matched AI keywords

    CONCEPT — Transparent Scoring:
        Every component is calculated separately. You can always audit why
        an article got a particular score by checking each component.
        This is the foundation of "explainable AI" — even without ML.
    """
    # Calculate each component
    recency_pts      = _score_recency(published_at)
    keyword_pts, matched = _score_keyword_relevance(title, description)
    credibility_pts  = _score_source_credibility(source)
    length_pts       = _score_content_length(description)

    # Sum all components (naturally capped at 100)
    total_score = recency_pts + keyword_pts + credibility_pts + length_pts
    total_score = max(0, min(100, total_score))  # Clamp to [0, 100]

    category = _get_score_category(total_score)
    keywords_found = ", ".join(matched) if matched else ""

    logger.debug(
        f"Score for '{str(title)[:40]}': "
        f"recency={recency_pts} + keywords={keyword_pts} "
        f"+ credibility={credibility_pts} + length={length_pts} "
        f"= {total_score} ({category})"
    )

    return total_score, category, keywords_found


def score_articles(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply AI News Intelligence Scoring to every article in the DataFrame.

    Adds three new columns to the DataFrame:
        - intelligence_score: Integer 0–100
        - score_category:     String label (Hot Trend / High Impact / Trending / Normal)
        - keywords_found:     Comma-separated list of matched AI keywords

    Args:
        df (pd.DataFrame): Validated and transformed articles.
                           Must have columns: title, description, source, published_at.

    Returns:
        pd.DataFrame: Original DataFrame with three new scoring columns appended.

    CONCEPT — Non-destructive:
        This function does NOT modify the input DataFrame.
        It returns a NEW DataFrame with the scoring columns added.
        The original df is preserved.
    """
    if df is None or df.empty:
        logger.warning("score_articles() received empty DataFrame.")
        return df

    logger.info(f"Scoring {len(df)} articles...")

    # Apply compute_article_score() to each row and collect results
    scores = []
    categories = []
    keywords_list = []

    for _, row in df.iterrows():
        score, category, keywords = compute_article_score(
            title=str(row.get("title", "") or ""),
            description=str(row.get("description", "") or ""),
            source=str(row.get("source", "") or ""),
            published_at=row.get("published_at"),
        )
        scores.append(score)
        categories.append(category)
        keywords_list.append(keywords)

    # Create a copy and add the new columns
    scored_df = df.copy()
    scored_df["intelligence_score"] = scores
    scored_df["score_category"]     = categories
    scored_df["keywords_found"]     = keywords_list

    # Log a distribution summary of scores
    avg_score = scored_df["intelligence_score"].mean()
    max_score = scored_df["intelligence_score"].max()
    min_score = scored_df["intelligence_score"].min()

    category_counts = scored_df["score_category"].value_counts().to_dict()

    logger.info(
        f"Scoring complete: avg={avg_score:.1f}, "
        f"max={max_score}, min={min_score}"
    )
    logger.info(f"Category distribution: {category_counts}")

    return scored_df
