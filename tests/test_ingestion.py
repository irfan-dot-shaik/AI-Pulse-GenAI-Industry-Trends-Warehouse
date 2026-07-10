# =============================================================================
# tests/test_ingestion.py — AI Pulse Project
# =============================================================================
#
# PURPOSE:
#   Unit tests for the ingestion pipeline (gnews_client.py).
#   These tests verify that our data transformation logic works correctly
#   WITHOUT making real API calls (no internet required).
#
# CONCEPT — What Is a Unit Test?
#   A unit test is a small, focused test that checks ONE specific behavior.
#   "Unit" means the smallest testable piece of code (usually one function).
#
#   Good unit tests:
#     ✓ Are fast (milliseconds, not seconds)
#     ✓ Are isolated (don't depend on external services like APIs or DBs)
#     ✓ Have clear names that describe what they test
#     ✓ Test one thing per test function
#
# CONCEPT — What Is Mocking?
#   "Mocking" means replacing a real dependency with a fake version.
#   Instead of calling the real GNews API (which needs internet + API key),
#   we create a "mock" response that pretends to be the real API.
#
#   Why mock?
#     1. Tests run without internet
#     2. Tests run without an API key
#     3. Tests run in milliseconds (no network delay)
#     4. Tests produce predictable results (API can return different data each time)
#
# CONCEPT — pytest:
#   pytest is the standard Python testing framework.
#   You run tests with: pytest tests/
#   pytest automatically finds all files named test_*.py
#   and all functions named test_*.
#
# HOW TO RUN:
#   From your project root: pytest tests/ -v
#   The -v flag means "verbose" — shows each test name and result.
#
# =============================================================================

import pytest                    # Testing framework
import pandas as pd              # For DataFrame assertions
from unittest.mock import patch, MagicMock  # For mocking API calls
from datetime import datetime


# =============================================================================
# Test Data (Fixtures)
# =============================================================================
# CONCEPT — Fixtures:
#   A fixture is sample data or setup code shared across multiple tests.
#   Instead of copying the same mock data into every test, we define it once.
#   pytest automatically passes fixtures to test functions that declare them
#   as parameters.
# =============================================================================

# A realistic sample of what the GNews API returns (JSON structure)
MOCK_GNEWS_RESPONSE = {
    "totalArticles": 2,
    "articles": [
        {
            "title": "OpenAI Releases GPT-5 with Major Improvements",
            "description": "OpenAI has unveiled GPT-5, its most powerful language model yet.",
            "content": "Full article content would go here...",
            "url": "https://techcrunch.com/2026/06/24/openai-gpt5",
            "image": "https://techcrunch.com/image.jpg",
            "publishedAt": "2026-06-24T10:00:00Z",
            "source": {
                "name": "TechCrunch",
                "url": "https://techcrunch.com"
            }
        },
        {
            "title": "Google Gemini Ultra 2.0 Beats All Benchmarks",
            "description": "Google's latest Gemini model achieves state-of-the-art results.",
            "content": "Full article content here...",
            "url": "https://wired.com/2026/06/24/gemini-ultra-2",
            "image": "https://wired.com/image.jpg",
            "publishedAt": "2026-06-23T15:30:00Z",
            "source": {
                "name": "Wired",
                "url": "https://wired.com"
            }
        }
    ]
}

# A sample with a missing URL (edge case — should be skipped)
MOCK_GNEWS_NO_URL = {
    "totalArticles": 1,
    "articles": [
        {
            "title": "Article Without URL",
            "description": "This article has no URL.",
            "content": "Content...",
            "url": "",  # Empty URL — should be skipped
            "publishedAt": "2026-06-24T10:00:00Z",
            "source": {"name": "Unknown", "url": ""}
        }
    ]
}


# =============================================================================
# Test: Successful API Fetch and Transformation
# =============================================================================

class TestFetchAiNews:
    """
    Tests for the fetch_ai_news() function in ingestion/gnews_client.py.

    CONCEPT — Test Classes:
        Grouping related tests into a class keeps them organized.
        pytest runs all methods starting with 'test_' automatically.
    """

    @patch("ingestion.gnews_client.requests.get")
    def test_returns_dataframe_on_success(self, mock_get):
        """
        TEST: fetch_ai_news() returns a DataFrame when the API is successful.

        WHAT WE'RE TESTING:
            Given a valid API response (2 articles),
            When we call fetch_ai_news(),
            Then we should get a non-empty DataFrame with 2 rows.

        HOW MOCKING WORKS HERE:
            @patch("ingestion.gnews_client.requests.get") replaces the
            requests.get function (inside gnews_client.py) with mock_get.
            We then configure mock_get to return our fake response.
        """
        # Arrange: set up the mock to return our fake data
        mock_response = MagicMock()                    # A fake response object
        mock_response.status_code = 200               # Pretend status is 200 OK
        mock_response.json.return_value = MOCK_GNEWS_RESPONSE  # Return fake JSON
        mock_response.raise_for_status.return_value = None     # No error raised

        mock_get.return_value = mock_response          # When requests.get() is called,
                                                       # return our fake response

        # Act: call the function we're testing
        from ingestion.gnews_client import fetch_ai_news
        result = fetch_ai_news()

        # Assert: verify the results are what we expect
        assert result is not None, "Expected a DataFrame, got None"
        assert isinstance(result, pd.DataFrame), "Result should be a pandas DataFrame"
        assert len(result) == 2, f"Expected 2 rows, got {len(result)}"

    @patch("ingestion.gnews_client.requests.get")
    def test_dataframe_has_correct_columns(self, mock_get):
        """
        TEST: The returned DataFrame has exactly the columns our DB schema expects.

        This ensures that the transformation logic produces columns that
        match the raw_ai_news table definition in models.py.
        """
        # Arrange
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = MOCK_GNEWS_RESPONSE
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        # Act
        from ingestion.gnews_client import fetch_ai_news
        result = fetch_ai_news()

        # Assert: check that all expected columns are present
        # NOTE: ingested_at is NOT in the DataFrame — PostgreSQL sets it
        # automatically via server_default=func.now() when the row is inserted.
        expected_columns = {
            "title", "source", "author", "description",
            "published_at", "url", "category"
        }
        actual_columns = set(result.columns)
        assert expected_columns == actual_columns, (
            f"Column mismatch.\n"
            f"Expected: {expected_columns}\n"
            f"Got:      {actual_columns}"
        )

    @patch("ingestion.gnews_client.requests.get")
    def test_url_column_has_correct_values(self, mock_get):
        """
        TEST: The URL column contains the correct values from the mock data.

        URL is our idempotency key — we must ensure it's correctly extracted.
        """
        # Arrange
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = MOCK_GNEWS_RESPONSE
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        # Act
        from ingestion.gnews_client import fetch_ai_news
        result = fetch_ai_news()

        # Assert: check URLs match our mock data
        expected_urls = [
            "https://techcrunch.com/2026/06/24/openai-gpt5",
            "https://wired.com/2026/06/24/gemini-ultra-2"
        ]
        actual_urls = list(result["url"])
        assert actual_urls == expected_urls, f"URLs don't match: {actual_urls}"

    @patch("ingestion.gnews_client.requests.get")
    def test_category_is_always_ai(self, mock_get):
        """
        TEST: All articles have category = 'AI'.

        In Week 1, all records come from the AI query, so category must be 'AI'.
        """
        # Arrange
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = MOCK_GNEWS_RESPONSE
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        # Act
        from ingestion.gnews_client import fetch_ai_news
        result = fetch_ai_news()

        # Assert: every row must have category = "AI"
        assert (result["category"] == "AI").all(), \
            "All articles should have category='AI'"

    @patch("ingestion.gnews_client.requests.get")
    def test_articles_without_url_are_skipped(self, mock_get):
        """
        TEST: Articles with empty URLs are skipped (not inserted into DataFrame).

        This is important for idempotency — we cannot deduplicate articles
        without a URL. Skipping them is safer than inserting them.
        """
        # Arrange: use mock data where the article has no URL
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = MOCK_GNEWS_NO_URL  # Article with empty URL
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        # Act
        from ingestion.gnews_client import fetch_ai_news
        result = fetch_ai_news()

        # Assert: function returns None (no valid articles to process)
        assert result is None, "Expected None when all articles have empty URLs"

    @patch("ingestion.gnews_client.requests.get")
    def test_returns_none_on_connection_error(self, mock_get):
        """
        TEST: fetch_ai_news() returns None when the API is unreachable.

        A pipeline should not crash the entire program when the API is down.
        It should gracefully return None and let the caller handle it.
        """
        import requests as req

        # Arrange: make requests.get() raise a ConnectionError
        mock_get.side_effect = req.exceptions.ConnectionError("Simulated network failure")

        # Act
        from ingestion.gnews_client import fetch_ai_news
        result = fetch_ai_news()

        # Assert: function returns None (not raise an exception)
        assert result is None, "Expected None on connection error, not an exception"

    @patch("ingestion.gnews_client.requests.get")
    def test_returns_none_on_http_error(self, mock_get):
        """
        TEST: fetch_ai_news() returns None when the API returns an error code.

        Example: API key is invalid → server returns 401 Unauthorized.
        The function should log the error and return None gracefully.
        """
        import requests as req

        # Arrange: make raise_for_status() raise an HTTPError
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = req.exceptions.HTTPError(
            "401 Client Error: Unauthorized"
        )
        mock_get.return_value = mock_response

        # Act
        from ingestion.gnews_client import fetch_ai_news
        result = fetch_ai_news()

        # Assert
        assert result is None, "Expected None on HTTP error"


# =============================================================================
# Test: DateTime Parsing
# =============================================================================

class TestParseDatetime:
    """
    Tests for the _parse_datetime() helper function.
    This function converts ISO 8601 strings to Python datetime objects.
    """

    def test_parses_valid_iso_string(self):
        """TEST: A valid ISO 8601 string is correctly parsed."""
        from ingestion.gnews_client import _parse_datetime

        result = _parse_datetime("2026-06-24T10:00:00Z")

        assert result is not None
        assert isinstance(result, datetime)
        assert result.year == 2026
        assert result.month == 6
        assert result.day == 24

    def test_returns_none_for_empty_string(self):
        """TEST: Empty string input returns None (graceful handling)."""
        from ingestion.gnews_client import _parse_datetime

        result = _parse_datetime("")
        assert result is None

    def test_returns_none_for_none_input(self):
        """TEST: None input returns None (no crash)."""
        from ingestion.gnews_client import _parse_datetime

        result = _parse_datetime(None)
        assert result is None

    def test_returns_none_for_invalid_format(self):
        """TEST: Malformed date string returns None (no crash)."""
        from ingestion.gnews_client import _parse_datetime

        result = _parse_datetime("not-a-date")
        assert result is None
