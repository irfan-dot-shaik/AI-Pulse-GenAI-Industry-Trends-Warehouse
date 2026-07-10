# =============================================================================
# ingestion/_utils.py — AI Pulse Project
# =============================================================================
#
# PURPOSE:
#   Shared utility functions used by ALL ingestion clients:
#     - gnews_client.py  (Week 1)
#     - hn_client.py     (Week 3)
#     - reddit_client.py (Week 3)
#
# CONCEPT — DRY (Don't Repeat Yourself):
#   Before this file existed, _parse_datetime() was a private function inside
#   gnews_client.py. When we added HN and Reddit clients, we had a choice:
#     a) Copy-paste the function into every client → divergence risk
#     b) Extract it into a shared module → single source of truth
#
#   Option (b) is the correct engineering decision. Any fix to datetime parsing
#   now benefits all three clients automatically.
#
# =============================================================================

from datetime import datetime, timezone
from typing import Optional

from utils.logger import get_logger

logger = get_logger(__name__)


def parse_datetime(dt_string: Optional[str]) -> Optional[datetime]:
    """
    Parse an ISO 8601 datetime string into a timezone-aware Python datetime.

    This function handles the format returned by GNews API and is also
    used for any ISO 8601 strings from other sources.

    Args:
        dt_string: ISO 8601 string, e.g. "2026-06-24T10:00:00Z".
                   Can be None.

    Returns:
        datetime: A timezone-aware datetime object (UTC), or None if parsing fails.

    CONCEPT — ISO 8601:
        The international standard for date/time strings.
        The "Z" at the end means UTC timezone (equivalent to +00:00).
        Example: "2026-06-24T10:30:00Z" = June 24, 2026, 10:30 AM UTC
    """
    if not dt_string:
        return None

    try:
        # Python 3.11+ fromisoformat() handles "Z" suffix natively.
        # The replace("Z", "+00:00") ensures compatibility with 3.10 as well.
        return datetime.fromisoformat(str(dt_string).replace("Z", "+00:00"))
    except (ValueError, AttributeError) as e:
        logger.warning(f"Could not parse datetime string '{dt_string}': {e}")
        return None


def parse_unix_timestamp(unix_ts: Optional[int]) -> Optional[datetime]:
    """
    Convert a Unix epoch timestamp (integer seconds) to a timezone-aware
    UTC datetime object.

    Used by Hacker News ingestion — HN provides timestamps as Unix integers.

    Args:
        unix_ts: Unix timestamp (seconds since 1970-01-01 00:00:00 UTC).
                 Can be None.

    Returns:
        datetime: A timezone-aware datetime object in UTC, or None on failure.

    CONCEPT — Unix Timestamp:
        Unix time counts seconds since January 1, 1970 at 00:00:00 UTC.
        Example: 1750000000 → 2025-06-15 06:13:20 UTC
        Python's datetime.fromtimestamp(..., tz=timezone.utc) converts it.
    """
    if unix_ts is None:
        return None

    try:
        return datetime.fromtimestamp(int(unix_ts), tz=timezone.utc)
    except (ValueError, TypeError, OSError) as e:
        logger.warning(f"Could not parse Unix timestamp '{unix_ts}': {e}")
        return None


def normalize_text(value: Optional[str], default: str = "") -> str:
    """
    Strip leading/trailing whitespace from a string value.

    Returns the default if value is None, empty, or whitespace-only.

    Args:
        value:   The string to normalize. Can be None.
        default: Value to return if input is empty after stripping.

    Returns:
        str: Stripped string, or default if empty.

    CONCEPT — Why Normalize at Ingestion?
        Data quality starts at the point of entry. Normalizing whitespace
        here means the downstream validator, transformer, and scorer all
        receive clean inputs without needing to handle raw edge cases.
    """
    if value is None:
        return default
    cleaned = str(value).strip()
    return cleaned if cleaned else default
