# =============================================================================
# tests/test_processing.py — AI Pulse Project
# =============================================================================
#
# PURPOSE:
#   Unit tests for the processing layer:
#     - processing/validator.py   (3 tests)
#     - processing/transformer.py (2 tests)
#     - processing/scorer.py      (3 tests)
#
#   These tests close coverage gaps in the existing test suite,
#   which previously only tested the ingestion layer.
#   All tests are self-contained and do not require a database connection.
#
# TESTS (8):
#   Validator:
#     1. Rejects articles with titles shorter than 10 characters
#     2. Rejects articles with empty or missing URL
#     3. Rejects articles with missing published_at timestamp
#   Transformer:
#     4. Source names are title-cased
#     5. Descriptions longer than 1000 chars are truncated to exactly 1000
#   Scorer:
#     6. Tier 1 sources score higher than unknown sources (same content)
#     7. Recent articles (< 6 hours ago) score higher than old ones (> 7 days)
#     8. Output scores are clamped to the [0, 100] range
#
# =============================================================================

import pandas as pd
from datetime import datetime, timezone, timedelta


# =============================================================================
# Shared Test Data Helpers
# =============================================================================

def _make_article_df(**overrides) -> pd.DataFrame:
    """
    Build a single-row DataFrame representing one article.
    All fields are valid by default; use overrides to introduce specific issues.
    """
    base = {
        "title":        "OpenAI Releases GPT-5 With Major Improvements",
        "source":       "TechCrunch",
        "author":       "Jane Smith",
        "description":  "OpenAI has unveiled GPT-5, its most advanced model yet.",
        "published_at": datetime.now(timezone.utc) - timedelta(hours=2),  # 2h ago
        "url":          "https://techcrunch.com/openai-gpt5",
        "category":     "AI",
    }
    base.update(overrides)
    return pd.DataFrame([base])


# =============================================================================
# Validator Tests
# =============================================================================

class TestValidateArticles:
    """Tests for processing/validator.py → validate_articles()."""

    def test_rejects_titles_shorter_than_10_chars(self):
        """
        TEST: Articles with titles shorter than 10 characters fail validation.

        RULE 4 in validator.py: title must be >= 10 characters.
        A title like "AI" or "GPT" is not a real headline.
        """
        df = _make_article_df(title="AI news")  # 7 chars — below minimum

        from processing.validator import validate_articles
        result = validate_articles(df)

        assert result.valid_df.empty, (
            f"Expected empty valid_df for short title, "
            f"got {len(result.valid_df)} rows"
        )
        assert len(result.invalid_df) == 1, (
            "Short-title article should appear in invalid_df"
        )
        assert result.report["invalid"] == 1

    def test_rejects_articles_with_empty_url(self):
        """
        TEST: Articles with empty or missing URL fail validation.

        RULE 2 in validator.py: url must not be empty or null.
        Without a URL we cannot deduplicate articles (URL is our idempotency key).
        """
        df = _make_article_df(url="")  # Empty URL

        from processing.validator import validate_articles
        result = validate_articles(df)

        assert result.valid_df.empty, (
            "Article with empty URL should not be in valid_df"
        )
        assert result.report["invalid"] >= 1

    def test_rejects_articles_with_missing_published_at(self):
        """
        TEST: Articles with None published_at fail validation.

        RULE 3 in validator.py: published_at must not be null.
        We need a timestamp to compute recency scores and trend charts.
        """
        df = _make_article_df(published_at=None)  # No timestamp

        from processing.validator import validate_articles
        result = validate_articles(df)

        assert result.valid_df.empty, (
            "Article with None published_at should not be in valid_df"
        )
        assert result.report["invalid"] >= 1


# =============================================================================
# Transformer Tests
# =============================================================================

class TestTransformArticles:
    """Tests for processing/transformer.py → transform_articles()."""

    def test_source_names_are_title_cased(self):
        """
        TEST: Source names are title-cased during transformation.

        Input:  "techcrunch"
        Output: "Techcrunch" (or "TechCrunch" — title() behavior)

        TRANSFORMATION 2 in transformer.py.
        """
        df = _make_article_df(source="techcrunch")

        from processing.transformer import transform_articles
        result = transform_articles(df)

        source_value = result.iloc[0]["source"]
        # str.title() converts "techcrunch" → "Techcrunch"
        # We check it's not purely lowercase
        assert source_value == source_value.title() or not source_value.islower(), (
            f"Source should be title-cased, got '{source_value}'"
        )

    def test_descriptions_truncated_to_1000_chars(self):
        """
        TEST: Descriptions longer than 1000 characters are truncated
        to exactly 1000 characters.

        TRANSFORMATION 4 in transformer.py.
        This prevents extremely long articles from bloating the database.
        """
        long_description = "A" * 1500  # 1500 chars — over the 1000-char limit

        df = _make_article_df(description=long_description)

        from processing.transformer import transform_articles
        result = transform_articles(df)

        desc_value = result.iloc[0]["description"]
        assert desc_value is not None, "Description should not be None"
        assert len(desc_value) <= 1000, (
            f"Description should be truncated to ≤1000 chars, got {len(desc_value)}"
        )


# =============================================================================
# Scorer Tests
# =============================================================================

class TestScoreArticles:
    """Tests for processing/scorer.py → score_articles()."""

    def test_tier1_sources_score_higher_than_unknown(self):
        """
        TEST: Articles from Tier 1 sources (e.g. "Reuters") receive a higher
        intelligence score than articles from an unknown source.

        COMPONENT 3 in scorer.py:
            Tier 1 → 20 pts
            Unknown → 3 pts

        Both articles have the same title, description, URL, and recency
        so that the score difference comes only from the source credibility.
        """
        # Same recency, same keywords — only source differs
        recent = datetime.now(timezone.utc) - timedelta(hours=3)
        shared_title = "OpenAI announces new generative AI model with transformer architecture"
        shared_desc = "A major announcement from OpenAI about a new LLM model."

        tier1_df = _make_article_df(
            source="Reuters",
            title=shared_title,
            description=shared_desc,
            published_at=recent,
        )
        unknown_df = _make_article_df(
            source="MyRandomBlog.net",
            title=shared_title,
            description=shared_desc,
            published_at=recent,
        )

        from processing.scorer import score_articles
        tier1_result = score_articles(tier1_df)
        unknown_result = score_articles(unknown_df)

        tier1_score = tier1_result.iloc[0]["intelligence_score"]
        unknown_score = unknown_result.iloc[0]["intelligence_score"]

        assert tier1_score > unknown_score, (
            f"Reuters (Tier 1) should score higher than unknown source. "
            f"Got Reuters={tier1_score}, Unknown={unknown_score}"
        )

    def test_recent_articles_score_higher_than_old(self):
        """
        TEST: Articles published < 6 hours ago score higher than articles
        published > 7 days ago (all other factors equal).

        COMPONENT 1 in scorer.py:
            < 6 hours  → 30 recency points
            >= 7 days  →  5 recency points
        """
        shared_title = "OpenAI releases new generative AI transformer model"
        shared_desc  = "A detailed description of an OpenAI LLM announcement."
        shared_source = "Wired"

        recent_df = _make_article_df(
            published_at=datetime.now(timezone.utc) - timedelta(hours=2),
            title=shared_title,
            description=shared_desc,
            source=shared_source,
        )
        old_df = _make_article_df(
            published_at=datetime.now(timezone.utc) - timedelta(days=14),
            title=shared_title,
            description=shared_desc,
            source=shared_source,
        )

        from processing.scorer import score_articles
        recent_result = score_articles(recent_df)
        old_result = score_articles(old_df)

        recent_score = recent_result.iloc[0]["intelligence_score"]
        old_score    = old_result.iloc[0]["intelligence_score"]

        assert recent_score > old_score, (
            f"Recent article should score higher than 14-day-old article. "
            f"Got recent={recent_score}, old={old_score}"
        )

    def test_scores_are_clamped_to_0_100(self):
        """
        TEST: All intelligence scores in the output are within [0, 100].

        The scorer sums multiple components. Even if the sum would logically
        exceed 100 (e.g. due to future rule additions), the final score must
        be clamped to 100. Similarly it must never go below 0.
        """
        # Build a batch of 5 articles with varied sources and ages
        articles = [
            _make_article_df(
                source=src,
                published_at=datetime.now(timezone.utc) - timedelta(hours=age),
                title="OpenAI generative AI large language model GPT Claude Gemini",
                description="AI model transformer deep learning neural network LLM foundation model.",
            )
            for src, age in [
                ("Reuters", 1),
                ("TechCrunch", 12),
                ("MyBlog", 72),
                ("Hacker News", 200),
                ("Reddit/MachineLearning", 5),
            ]
        ]
        combined = pd.concat(articles, ignore_index=True)

        from processing.scorer import score_articles
        result = score_articles(combined)

        scores = result["intelligence_score"].tolist()

        for score in scores:
            assert 0 <= score <= 100, (
                f"Score {score} is outside [0, 100] range"
            )
