# =============================================================================
# processing/validator.py — AI Pulse Project
# =============================================================================
#
# PURPOSE:
#   Validates raw articles fetched from the GNews API before they are
#   processed and written to the staging layer (stg_ai_news).
#
# CONCEPT — Why Validate Data?
#   Garbage In = Garbage Out. If incomplete or malformed records enter your
#   warehouse, every downstream report, chart, and insight will be wrong.
#   Validation is the first line of defense in a data quality strategy.
#
# CONCEPT — The Three V's of Validation:
#   1. Validity   — Does the data match expected format/type?
#   2. Completeness — Are required fields present and non-empty?
#   3. Consistency  — Does the data make logical sense?
#
# VALIDATION RULES (Week 2):
#   RULE 1: 'title' must not be empty, null, or the placeholder "No Title"
#   RULE 2: 'url' must not be empty or null
#   RULE 3: 'published_at' must not be null (we need it for scoring recency)
#   RULE 4: 'title' must be at least 10 characters (avoids garbage titles)
#   RULE 5: 'url' must start with 'http' (basic URL format check)
#
# OUTPUT:
#   Returns a named tuple with:
#     - valid_df:       DataFrame of articles that passed all rules
#     - invalid_df:     DataFrame of rejected articles (for logging/audit)
#     - report:         Dictionary summarizing the validation results
#
# =============================================================================

import pandas as pd                   # DataFrame manipulation
from typing import NamedTuple          # For typed return value
from utils.logger import get_logger   # Our centralized logger

logger = get_logger(__name__)


# =============================================================================
# Validation Result Container
# =============================================================================
# CONCEPT — NamedTuple:
#   A NamedTuple is like a regular tuple but with named fields.
#   Instead of result[0], you write result.valid_df — much more readable.
#   It's immutable (cannot be changed after creation), which is safe for
#   passing around validation results.
# =============================================================================

class ValidationResult(NamedTuple):
    """
    Container for the output of validate_articles().

    Attributes:
        valid_df:   Articles that passed all validation rules.
        invalid_df: Articles that failed at least one rule.
        report:     Summary dict with counts and rejection reasons.
    """
    valid_df: pd.DataFrame
    invalid_df: pd.DataFrame
    report: dict


# =============================================================================
# Validation Rules
# =============================================================================
# Each rule is a small function that takes a single row (pd.Series) and
# returns a tuple: (passed: bool, reason: str)
#
# CONCEPT — Small Functions:
#   Instead of one giant if-else block, each rule is its own function.
#   This makes it easy to:
#     - Add new rules without touching existing ones
#     - Test each rule independently
#     - Turn rules on/off with a simple list
# =============================================================================

def _rule_title_not_empty(row: pd.Series) -> tuple[bool, str]:
    """RULE 1: Title must be present, non-empty, and not the placeholder."""
    title = str(row.get("title", "") or "").strip()
    if not title or title.lower() == "no title":
        return False, "Missing or placeholder title"
    return True, ""


def _rule_title_min_length(row: pd.Series) -> tuple[bool, str]:
    """RULE 2: Title must be at least 10 characters (filters noise/garbage)."""
    title = str(row.get("title", "") or "").strip()
    if len(title) < 10:
        return False, f"Title too short ({len(title)} chars, minimum 10)"
    return True, ""


def _rule_url_not_empty(row: pd.Series) -> tuple[bool, str]:
    """RULE 3: URL must be present and non-empty."""
    url = str(row.get("url", "") or "").strip()
    if not url:
        return False, "Missing URL"
    return True, ""


def _rule_url_format(row: pd.Series) -> tuple[bool, str]:
    """RULE 4: URL must start with http (basic format check)."""
    url = str(row.get("url", "") or "").strip()
    if url and not url.startswith("http"):
        return False, f"Invalid URL format (must start with 'http'): {url[:50]}"
    return True, ""


def _rule_published_at_not_null(row: pd.Series) -> tuple[bool, str]:
    """RULE 5: published_at must not be null (required for recency scoring)."""
    published_at = row.get("published_at")
    if published_at is None or (hasattr(published_at, '__class__')
                                 and published_at.__class__.__name__ == 'NaTType'):
        return False, "Missing published_at timestamp"
    # Check for pandas NaT (Not a Timestamp)
    try:
        import pandas as pd  # noqa: F811
        if pd.isnull(published_at):
            return False, "published_at is NaT (Not a Timestamp)"
    except (TypeError, ValueError):
        pass  # If pd.isnull throws, the value is probably valid
    return True, ""


# Ordered list of all validation rules to apply
# CONCEPT: By using a list, you can easily add/remove/reorder rules
VALIDATION_RULES = [
    _rule_title_not_empty,
    _rule_title_min_length,
    _rule_url_not_empty,
    _rule_url_format,
    _rule_published_at_not_null,
]


# =============================================================================
# Main Validation Function
# =============================================================================

def validate_articles(df: pd.DataFrame) -> ValidationResult:
    """
    Apply all validation rules to a DataFrame of raw articles.

    Each row is tested against every rule in VALIDATION_RULES.
    A row is considered VALID only if ALL rules pass.
    A row is INVALID if ANY rule fails.

    The validation_notes column records the FIRST failure reason for each
    invalid row, making it easy to audit and fix issues.

    Args:
        df (pd.DataFrame): Raw articles from fetch_ai_news() or raw_ai_news table.

    Returns:
        ValidationResult: NamedTuple containing valid_df, invalid_df, report.

    Example:
        result = validate_articles(raw_df)
        print(f"Valid: {len(result.valid_df)}, Invalid: {len(result.invalid_df)}")
        result.valid_df  # Pass to transform_articles()
    """
    if df is None or df.empty:
        logger.warning("validate_articles() received empty DataFrame. Returning empty result.")
        empty = pd.DataFrame(columns=df.columns if df is not None else [])
        return ValidationResult(
            valid_df=empty,
            invalid_df=empty,
            report={"total": 0, "valid": 0, "invalid": 0, "rejection_reasons": {}}
        )

    logger.info(f"Starting validation of {len(df)} articles...")

    # Track results per row
    valid_indices = []
    invalid_indices = []
    rejection_reasons = {}  # Maps index → first failure reason

    for idx, row in df.iterrows():
        row_passed = True
        first_failure_reason = ""

        # Apply each rule in order; stop at first failure
        for rule_fn in VALIDATION_RULES:
            passed, reason = rule_fn(row)
            if not passed:
                row_passed = False
                first_failure_reason = reason
                # Track how many times each reason appears
                rejection_reasons[reason] = rejection_reasons.get(reason, 0) + 1
                break  # Stop checking remaining rules for this row

        if row_passed:
            valid_indices.append(idx)
        else:
            invalid_indices.append(idx)
            logger.debug(
                f"Article rejected [{idx}] "
                f"'{str(row.get('title', ''))[:40]}...' "
                f"Reason: {first_failure_reason}"
            )

    # Build the valid and invalid DataFrames
    valid_df = df.loc[valid_indices].copy()
    invalid_df = df.loc[invalid_indices].copy()

    # Add validation_notes column to invalid_df for audit trail
    if not invalid_df.empty:
        # Re-run rules to attach reasons (for the invalid_df only)
        notes = []
        for idx, row in invalid_df.iterrows():
            for rule_fn in VALIDATION_RULES:
                passed, reason = rule_fn(row)
                if not passed:
                    notes.append(reason)
                    break
            else:
                notes.append("Unknown validation failure")
        invalid_df = invalid_df.copy()
        invalid_df["validation_notes"] = notes

    # Build the quality report
    report = {
        "total":             len(df),
        "valid":             len(valid_df),
        "invalid":           len(invalid_df),
        "pass_rate_pct":     round(len(valid_df) / len(df) * 100, 1) if len(df) > 0 else 0,
        "rejection_reasons": rejection_reasons,
    }

    # Log the summary
    logger.info(
        f"Validation complete: {report['valid']} valid, "
        f"{report['invalid']} invalid "
        f"({report['pass_rate_pct']}% pass rate)"
    )
    if rejection_reasons:
        logger.info("Rejection breakdown:")
        for reason, count in rejection_reasons.items():
            logger.info(f"  - '{reason}': {count} article(s)")

    return ValidationResult(valid_df=valid_df, invalid_df=invalid_df, report=report)
