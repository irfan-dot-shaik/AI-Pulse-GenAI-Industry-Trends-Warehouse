# =============================================================================
# tests/test_reddit_client.py — AI Pulse Project
# =============================================================================
#
# PURPOSE:
#   Unit tests for ingestion/reddit_client.py.
#   All tests mock PRAW — no real Reddit API calls are made.
#   Reddit credentials are temporarily patched to non-empty strings
#   to allow the function to proceed past the credential check.
#
# TESTS (6):
#   1. Returns DataFrame on a successful fetch
#   2. DataFrame has the correct 7-column pipeline schema
#   3. Self-post URLs (reddit.com) are filtered out
#   4. Returns None when credentials are not configured
#   5. Returns None when the subreddit has no external-link posts
#   6. Source column contains the subreddit name
#
# =============================================================================

import pytest
import pandas as pd
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone


# =============================================================================
# Mock Post Builder
# =============================================================================

def _make_mock_post(
    title: str = "OpenAI releases GPT-5 with incredible new capabilities",
    url: str = "https://techcrunch.com/openai-gpt5",
    selftext: str = "",
    author: str = "test_redditor",
    created_utc: float = 1750000000.0,
) -> MagicMock:
    """Build a mock PRAW Submission object with the given fields."""
    post = MagicMock()
    post.title = title
    post.url = url
    post.selftext = selftext
    post.author = MagicMock()
    post.author.__str__ = lambda self: author
    post.created_utc = created_utc
    return post


# A post with an external article URL (should be kept)
_EXTERNAL_POST = _make_mock_post(
    title="Google DeepMind announces Gemini Ultra 2 with major breakthroughs",
    url="https://deepmind.google/blog/gemini-ultra-2",
)

# A self-post (URL points back to Reddit — should be filtered out)
_SELF_POST = _make_mock_post(
    title="Discussion: What do you think of the latest GPT-4o update?",
    url="https://www.reddit.com/r/MachineLearning/comments/abc123/discussion",
)

# A post with an image URL (should be filtered out)
_IMAGE_POST = _make_mock_post(
    title="Architecture diagram of a transformer neural network",
    url="https://i.redd.it/some_image.png",
)


def _make_mock_subreddit(posts: list[MagicMock]) -> MagicMock:
    """Create a mock PRAW Subreddit whose .hot() returns the given posts."""
    subreddit = MagicMock()
    subreddit.hot.return_value = iter(posts)
    return subreddit


# =============================================================================
# Tests
# =============================================================================

class TestFetchRedditNews:
    """Tests for fetch_reddit_news() in ingestion/reddit_client.py."""

    @patch("ingestion.reddit_client._PRAW_AVAILABLE", True)
    @patch("ingestion.reddit_client.REDDIT_CLIENT_ID", "fake_id")
    @patch("ingestion.reddit_client.REDDIT_CLIENT_SECRET", "fake_secret")
    @patch("ingestion.reddit_client.praw")
    def test_returns_dataframe_on_success(self, mock_praw):
        """
        TEST: fetch_reddit_news() returns a non-empty DataFrame when at least
        one external-link post is found.

        MOCK STRATEGY:
            Patch praw.Reddit() to return a mock instance whose .subreddit()
            yields a single external-link post.
        """
        mock_reddit = MagicMock()
        mock_praw.Reddit.return_value = mock_reddit
        mock_reddit.subreddit.return_value = _make_mock_subreddit([_EXTERNAL_POST])

        from ingestion.reddit_client import fetch_reddit_news
        result = fetch_reddit_news(subreddits=["MachineLearning"], limit=5)

        assert result is not None, "Expected a DataFrame, got None"
        assert isinstance(result, pd.DataFrame)
        assert len(result) >= 1

    @patch("ingestion.reddit_client._PRAW_AVAILABLE", True)
    @patch("ingestion.reddit_client.REDDIT_CLIENT_ID", "fake_id")
    @patch("ingestion.reddit_client.REDDIT_CLIENT_SECRET", "fake_secret")
    @patch("ingestion.reddit_client.praw")
    def test_dataframe_has_correct_columns(self, mock_praw):
        """
        TEST: The returned DataFrame has exactly the 7 columns required
        by the raw pipeline schema.
        """
        mock_reddit = MagicMock()
        mock_praw.Reddit.return_value = mock_reddit
        mock_reddit.subreddit.return_value = _make_mock_subreddit([_EXTERNAL_POST])

        from ingestion.reddit_client import fetch_reddit_news
        result = fetch_reddit_news(subreddits=["MachineLearning"], limit=5)

        assert result is not None
        expected_columns = {
            "title", "source", "author", "description",
            "published_at", "url", "category"
        }
        assert set(result.columns) == expected_columns, (
            f"Column mismatch.\nExpected: {expected_columns}\nGot: {set(result.columns)}"
        )

    @patch("ingestion.reddit_client._PRAW_AVAILABLE", True)
    @patch("ingestion.reddit_client.REDDIT_CLIENT_ID", "fake_id")
    @patch("ingestion.reddit_client.REDDIT_CLIENT_SECRET", "fake_secret")
    @patch("ingestion.reddit_client.praw")
    def test_self_post_urls_are_filtered_out(self, mock_praw):
        """
        TEST: Posts whose URLs point back to reddit.com (self-posts) are
        excluded from the returned DataFrame.

        Self-posts are discussion threads — they have no external article.
        Including them would insert duplicate/spam URLs into the warehouse.
        """
        mock_reddit = MagicMock()
        mock_praw.Reddit.return_value = mock_reddit
        # Only self-posts and image posts — no external articles
        mock_reddit.subreddit.return_value = _make_mock_subreddit(
            [_SELF_POST, _IMAGE_POST]
        )

        from ingestion.reddit_client import fetch_reddit_news
        result = fetch_reddit_news(subreddits=["MachineLearning"], limit=5)

        assert result is None, (
            "Expected None when all posts are self-posts or media, "
            f"but got DataFrame with {len(result) if result is not None else 0} rows"
        )

    @patch("ingestion.reddit_client.REDDIT_CLIENT_ID", "")
    @patch("ingestion.reddit_client.REDDIT_CLIENT_SECRET", "")
    def test_returns_none_when_credentials_not_configured(self):
        """
        TEST: Returns None immediately when REDDIT_CLIENT_ID or
        REDDIT_CLIENT_SECRET are empty.

        This is the graceful skip path used by main.py when Reddit
        credentials are not in .env.
        """
        from ingestion.reddit_client import fetch_reddit_news
        result = fetch_reddit_news(subreddits=["MachineLearning"], limit=5)

        assert result is None, (
            "Expected None when credentials are absent, "
            f"but got: {result}"
        )

    @patch("ingestion.reddit_client._PRAW_AVAILABLE", True)
    @patch("ingestion.reddit_client.REDDIT_CLIENT_ID", "fake_id")
    @patch("ingestion.reddit_client.REDDIT_CLIENT_SECRET", "fake_secret")
    @patch("ingestion.reddit_client.praw")
    def test_returns_none_when_no_external_posts(self, mock_praw):
        """
        TEST: Returns None when all posts in all subreddits are self-posts
        or media posts (no external article links).
        """
        mock_reddit = MagicMock()
        mock_praw.Reddit.return_value = mock_reddit
        mock_reddit.subreddit.return_value = _make_mock_subreddit([_SELF_POST])

        from ingestion.reddit_client import fetch_reddit_news
        result = fetch_reddit_news(subreddits=["MachineLearning"], limit=5)

        assert result is None

    @patch("ingestion.reddit_client._PRAW_AVAILABLE", True)
    @patch("ingestion.reddit_client.REDDIT_CLIENT_ID", "fake_id")
    @patch("ingestion.reddit_client.REDDIT_CLIENT_SECRET", "fake_secret")
    @patch("ingestion.reddit_client.praw")
    def test_source_column_contains_subreddit_name(self, mock_praw):
        """
        TEST: The `source` column is set to "Reddit/<SubredditName>".

        This is critical for the Source Analytics page, which groups
        articles by source to show per-subreddit breakdowns.
        """
        mock_reddit = MagicMock()
        mock_praw.Reddit.return_value = mock_reddit
        mock_reddit.subreddit.return_value = _make_mock_subreddit([_EXTERNAL_POST])

        from ingestion.reddit_client import fetch_reddit_news
        result = fetch_reddit_news(subreddits=["MachineLearning"], limit=5)

        assert result is not None
        source_value = result.iloc[0]["source"]
        assert source_value == "Reddit/MachineLearning", (
            f"Expected 'Reddit/MachineLearning', got '{source_value}'"
        )
