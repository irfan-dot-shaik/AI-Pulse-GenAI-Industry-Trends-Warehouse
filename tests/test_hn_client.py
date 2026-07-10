# =============================================================================
# tests/test_hn_client.py — AI Pulse Project
# =============================================================================
#
# PURPOSE:
#   Unit tests for ingestion/hn_client.py.
#   All tests mock HTTP calls — no real HN API requests are made.
#
# TESTS (5):
#   1. Returns DataFrame on a successful multi-feed fetch
#   2. DataFrame has the correct 7-column pipeline schema
#   3. Non-AI stories are filtered out by keyword filter
#   4. Unix timestamp is correctly converted to UTC datetime
#   5. Returns None when no AI-relevant stories are found
#
# =============================================================================

import pytest
import pandas as pd
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone


# =============================================================================
# Mock Data
# =============================================================================

# Minimal mock for a HN story that IS AI-relevant
_AI_STORY = {
    "id": 12345,
    "type": "story",
    "title": "OpenAI releases new GPT model with reasoning capabilities",
    "url": "https://techcrunch.com/openai-gpt-reasoning",
    "by": "test_user",
    "time": 1750000000,  # Unix timestamp → some UTC datetime in 2025
    "score": 500,
    "dead": False,
    "deleted": False,
}

# A HN story whose title contains NO AI keywords
_NON_AI_STORY = {
    "id": 99999,
    "type": "story",
    "title": "Rust 2.0 released with new memory model",
    "url": "https://blog.rust-lang.org/2025/rust-2",
    "by": "rust_fan",
    "time": 1750000100,
    "score": 200,
    "dead": False,
    "deleted": False,
}

# A story with no URL (Ask HN, Show HN without external link)
_NO_URL_STORY = {
    "id": 11111,
    "type": "story",
    "title": "Ask HN: Which LLM should I use for my startup?",
    "url": None,
    "by": "hacker",
    "time": 1750000200,
    "score": 100,
    "dead": False,
    "deleted": False,
}

# The three feed endpoints return lists of IDs
_FEED_IDS = [12345, 99999, 11111]


def _make_feed_response(ids: list[int]) -> MagicMock:
    """Create a mock response for a feed endpoint."""
    resp = MagicMock()
    resp.status_code = 200
    resp.json.return_value = ids
    resp.raise_for_status.return_value = None
    return resp


def _make_story_response(story: dict) -> MagicMock:
    """Create a mock response for a story detail endpoint."""
    resp = MagicMock()
    resp.status_code = 200
    resp.json.return_value = story
    resp.raise_for_status.return_value = None
    return resp


# =============================================================================
# Tests
# =============================================================================

class TestFetchHnNews:
    """Tests for fetch_hn_news() in ingestion/hn_client.py."""

    @patch("ingestion.hn_client.requests.get")
    def test_returns_dataframe_on_success(self, mock_get):
        """
        TEST: fetch_hn_news() returns a non-empty DataFrame when at least one
        AI-relevant story is found in the feed.

        MOCK STRATEGY:
            First 3 calls return the feed ID lists (topstories, beststories, newstories).
            Subsequent calls return individual story JSON.
            Only the AI story passes the keyword filter; the Rust story and
            no-URL story are skipped.
        """
        # Arrange
        mock_get.side_effect = [
            _make_feed_response([12345, 99999, 11111]),  # topstories
            _make_feed_response([12345]),                 # beststories
            _make_feed_response([99999]),                 # newstories
            _make_story_response(_AI_STORY),             # item/12345
            _make_story_response(_NON_AI_STORY),         # item/99999
            _make_story_response(_NO_URL_STORY),         # item/11111
        ]

        from ingestion.hn_client import fetch_hn_news
        result = fetch_hn_news(limit=5)

        assert result is not None, "Expected a DataFrame, got None"
        assert isinstance(result, pd.DataFrame), "Result should be a pandas DataFrame"
        assert len(result) >= 1, "Expected at least 1 AI article"

    @patch("ingestion.hn_client.requests.get")
    def test_dataframe_has_correct_columns(self, mock_get):
        """
        TEST: The returned DataFrame has exactly the 7 columns required
        by the raw pipeline schema.
        """
        mock_get.side_effect = [
            _make_feed_response([12345]),  # topstories
            _make_feed_response([]),       # beststories
            _make_feed_response([]),       # newstories
            _make_story_response(_AI_STORY),
        ]

        from ingestion.hn_client import fetch_hn_news
        result = fetch_hn_news(limit=5)

        assert result is not None
        expected_columns = {
            "title", "source", "author", "description",
            "published_at", "url", "category"
        }
        assert set(result.columns) == expected_columns, (
            f"Column mismatch.\nExpected: {expected_columns}\nGot: {set(result.columns)}"
        )

    @patch("ingestion.hn_client.requests.get")
    def test_non_ai_stories_are_filtered_out(self, mock_get):
        """
        TEST: Stories whose titles contain no AI keywords are NOT included
        in the returned DataFrame.
        """
        mock_get.side_effect = [
            _make_feed_response([99999]),  # topstories — Rust story only
            _make_feed_response([]),       # beststories
            _make_feed_response([]),       # newstories
            _make_story_response(_NON_AI_STORY),
        ]

        from ingestion.hn_client import fetch_hn_news
        result = fetch_hn_news(limit=5)

        # The Rust story should be filtered out → None returned
        assert result is None, (
            "Expected None when all stories are non-AI, "
            f"but got DataFrame with {len(result) if result is not None else 0} rows"
        )

    @patch("ingestion.hn_client.requests.get")
    def test_unix_timestamp_converted_to_utc_datetime(self, mock_get):
        """
        TEST: The `published_at` column contains a timezone-aware UTC datetime
        object corresponding to the Unix timestamp in the story JSON.

        The mock story has time=1750000000.
        datetime.fromtimestamp(1750000000, tz=UTC) must equal the result.
        """
        mock_get.side_effect = [
            _make_feed_response([12345]),
            _make_feed_response([]),
            _make_feed_response([]),
            _make_story_response(_AI_STORY),
        ]

        from ingestion.hn_client import fetch_hn_news
        result = fetch_hn_news(limit=5)

        assert result is not None
        published_at = result.iloc[0]["published_at"]

        assert published_at is not None, "published_at should not be None"
        assert isinstance(published_at, datetime), \
            f"published_at should be datetime, got {type(published_at)}"

        expected_dt = datetime.fromtimestamp(1750000000, tz=timezone.utc)
        assert published_at == expected_dt, (
            f"Timestamp mismatch.\nExpected: {expected_dt}\nGot: {published_at}"
        )

    @patch("ingestion.hn_client.requests.get")
    def test_returns_none_when_no_ai_stories_found(self, mock_get):
        """
        TEST: Returns None when the feeds contain only non-AI stories.

        This is the graceful empty-result path — the pipeline should not
        crash when HN happens to have no AI content in the top stories.
        """
        mock_get.side_effect = [
            _make_feed_response([99999]),  # Only Rust story
            _make_feed_response([]),
            _make_feed_response([]),
            _make_story_response(_NON_AI_STORY),
        ]

        from ingestion.hn_client import fetch_hn_news
        result = fetch_hn_news(limit=5)

        assert result is None, "Expected None when no AI stories are found"
