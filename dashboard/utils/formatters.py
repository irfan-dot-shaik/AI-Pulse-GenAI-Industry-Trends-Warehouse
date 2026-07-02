# =============================================================================
# dashboard/utils/formatters.py — AI Pulse Dashboard
# =============================================================================
#
# PURPOSE:
#   Utility functions for formatting raw data values into human-readable
#   strings for display in the dashboard.
#
# CONCEPT — Separation of Concerns:
#   Formatting logic should NOT live inside chart or component functions.
#   By centralizing formatting here, every component calls the same function
#   and the output is always consistent (e.g., "1,250 articles" everywhere).
#
# =============================================================================

from datetime import datetime, timezone
from typing import Optional


def format_number(n: int) -> str:
    """
    Format a large integer with comma thousands separator.

    Examples:
        1250   -> "1,250"
        42     -> "42"
        100000 -> "100,000"

    Args:
        n: Integer to format.

    Returns:
        str: Comma-formatted number string.
    """
    if n is None:
        return "0"
    return f"{int(n):,}"


def format_score(score: float) -> str:
    """
    Format an intelligence score as "XX / 100".

    Examples:
        87.0 -> "87 / 100"
        58.4 -> "58 / 100"

    Args:
        score: Float score value.

    Returns:
        str: Score display string.
    """
    if score is None:
        return "0 / 100"
    return f"{int(score)} / 100"


def format_score_badge(score: int) -> str:
    """
    Return a score with emoji badge based on category.

    Examples:
        95 -> "🔥 95"
        80 -> "⚡ 80"
        60 -> "📈 60"
        30 -> "📰 30"

    Args:
        score: Integer intelligence score (0-100).

    Returns:
        str: Emoji + score string.
    """
    if score >= 90:
        return f"🔥 {score}"
    elif score >= 75:
        return f"⚡ {score}"
    elif score >= 50:
        return f"📈 {score}"
    else:
        return f"📰 {score}"


def format_category_badge(category: str) -> str:
    """
    Return a colored label string for a score category.

    Args:
        category: One of "Hot Trend", "High Impact", "Trending", "Normal".

    Returns:
        str: Emoji + category string.
    """
    badges = {
        "Hot Trend":   "🔥 Hot Trend",
        "High Impact": "⚡ High Impact",
        "Trending":    "📈 Trending",
        "Normal":      "📰 Normal",
    }
    return badges.get(category, f"📰 {category}")


def format_relative_time(dt) -> str:
    """
    Format a datetime as a human-readable relative time string.

    Examples:
        2 hours ago     -> "2h ago"
        1 day ago       -> "1d ago"
        3 days ago      -> "3d ago"
        Just now        -> "Just now"

    Args:
        dt: datetime object or pandas Timestamp. Can be timezone-aware or naive.

    Returns:
        str: Relative time string.
    """
    if dt is None:
        return "Unknown"

    try:
        now = datetime.now(timezone.utc)

        # Handle pandas Timestamp
        if hasattr(dt, 'to_pydatetime'):
            dt = dt.to_pydatetime()

        # Make timezone-aware if naive
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)

        delta = now - dt
        total_seconds = delta.total_seconds()

        if total_seconds < 60:
            return "Just now"
        elif total_seconds < 3600:
            mins = int(total_seconds / 60)
            return f"{mins}m ago"
        elif total_seconds < 86400:
            hours = int(total_seconds / 3600)
            return f"{hours}h ago"
        elif total_seconds < 604800:
            days = int(total_seconds / 86400)
            return f"{days}d ago"
        else:
            weeks = int(total_seconds / 604800)
            return f"{weeks}w ago"
    except Exception:
        return str(dt)[:10]


def format_datetime_display(dt) -> str:
    """
    Format a datetime for display in article cards.

    Example: "Jul 02, 2026 at 15:30 UTC"

    Args:
        dt: datetime or pandas Timestamp.

    Returns:
        str: Formatted date string.
    """
    if dt is None:
        return "Unknown date"
    try:
        if hasattr(dt, 'to_pydatetime'):
            dt = dt.to_pydatetime()
        return dt.strftime("%b %d, %Y at %H:%M UTC")
    except Exception:
        return str(dt)[:19]


def format_keywords(keywords_str: str) -> list[str]:
    """
    Parse the comma-separated keywords_found string into a list.

    Args:
        keywords_str: Comma-separated string like "openai, gpt, llm".

    Returns:
        list[str]: List of individual keyword strings.
    """
    if not keywords_str:
        return []
    return [k.strip() for k in keywords_str.split(",") if k.strip()]


def truncate_text(text: str, max_chars: int = 120) -> str:
    """
    Truncate text to max_chars and append "..." if truncated.

    Used for description previews in article cards.

    Args:
        text:      Text to truncate.
        max_chars: Maximum allowed length (default 120 for card previews).

    Returns:
        str: Original or truncated string.
    """
    if not text:
        return ""
    text = str(text).strip()
    if len(text) <= max_chars:
        return text
    return text[:max_chars - 3] + "..."


def get_score_color(score: int) -> str:
    """
    Return a hex color string corresponding to an intelligence score.

    Used for coloring score badges in charts and cards.

    Args:
        score: Integer score 0-100.

    Returns:
        str: Hex color string.
    """
    if score >= 90:
        return "#EF4444"   # Red (hot/urgent)
    elif score >= 75:
        return "#F59E0B"   # Amber (high impact)
    elif score >= 50:
        return "#3B82F6"   # Blue (trending)
    else:
        return "#6B7280"   # Gray (normal)


def get_category_color(category: str) -> str:
    """
    Return a hex color for a score category label.

    Consistent with get_score_color() thresholds.

    Args:
        category: "Hot Trend", "High Impact", "Trending", or "Normal".

    Returns:
        str: Hex color string.
    """
    colors = {
        "Hot Trend":   "#EF4444",  # Red
        "High Impact": "#F59E0B",  # Amber
        "Trending":    "#3B82F6",  # Blue
        "Normal":      "#6B7280",  # Gray
    }
    return colors.get(category, "#6B7280")
