# =============================================================================
# ingestion/gnews_client.py — AI Pulse Project
# =============================================================================
#
# PURPOSE:
#   This module is responsible for fetching AI news articles from the GNews API
#   and transforming the raw JSON response into a clean Pandas DataFrame.
#
# CONCEPT — What Is an API?
#   An API (Application Programming Interface) is a way for two programs to talk.
#   The GNews API is a web service. We send an HTTP GET request with our API key
#   and query, and it returns a JSON response containing news articles.
#
# CONCEPT — What Is JSON?
#   JSON (JavaScript Object Notation) is a text format for structured data.
#   Example:
#   {
#     "title": "OpenAI releases GPT-5",
#     "source": {"name": "TechCrunch"},
#     "publishedAt": "2026-06-24T10:00:00Z"
#   }
#
# CONCEPT — What Is a DataFrame?
#   A DataFrame is a table-like data structure from the Pandas library.
#   Think of it as an Excel spreadsheet in Python:
#     - Rows = individual news articles
#     - Columns = article attributes (title, source, author, etc.)
#
# CONCEPT — Separation of Concerns:
#   This file ONLY handles fetching and transforming data.
#   It does NOT know about databases, logging files, or UI.
#   The database layer (warehouse.py) handles saving to PostgreSQL.
#   This makes the code easier to test, debug, and extend.
#
# FLOW:
#   GNews API → HTTP GET Request → JSON Response → Pandas DataFrame
#
# =============================================================================

import requests                  # HTTP library: makes API calls over the internet
import pandas as pd              # Data manipulation: transforms JSON into DataFrame
from datetime import datetime    # For timestamp parsing
from typing import Optional      # Type hint: for Optional[DataFrame] return type

# Import our project's config and logger
from config.settings import (
    GNEWS_API_KEY,
    GNEWS_BASE_URL,
    GNEWS_QUERY,
    GNEWS_MAX_RESULTS,
    GNEWS_LANGUAGE,
    GNEWS_COUNTRY,
    GNEWS_CATEGORY,
)
from utils.logger import get_logger

# Week 3: shared datetime parser (moved to ingestion/_utils.py)
# The alias below keeps all existing tests passing without modification.
from ingestion._utils import parse_datetime as _parse_datetime


# Create a logger specifically for this module
# __name__ here equals "ingestion.gnews_client"
logger = get_logger(__name__)


# =============================================================================
# GNews API Response Structure (for reference)
# =============================================================================
# When you call the GNews API, it returns JSON shaped like this:
#
# {
#   "totalArticles": 42,
#   "articles": [
#     {
#       "title": "OpenAI releases GPT-5",
#       "description": "OpenAI today announced...",
#       "content": "Full article text...",
#       "url": "https://techcrunch.com/...",
#       "image": "https://techcrunch.com/image.jpg",
#       "publishedAt": "2026-06-24T10:00:00Z",
#       "source": {
#         "name": "TechCrunch",
#         "url": "https://techcrunch.com"
#       }
#     },
#     { ... more articles ... }
#   ]
# }
#
# Notice: GNews does not provide an "author" field directly.
# We handle this gracefully by defaulting to "Unknown".
# =============================================================================


def fetch_ai_news() -> Optional[pd.DataFrame]:
    """
    Fetch AI-related news articles from the GNews API.

    This function:
      1. Builds the API request with the correct parameters
      2. Sends an HTTP GET request to GNews
      3. Validates the response (checks for errors)
      4. Parses the JSON response into a list of articles
      5. Transforms each article into a structured dictionary
      6. Returns a clean Pandas DataFrame

    Returns:
        pd.DataFrame: A DataFrame where each row is one news article.
                      Returns None if the fetch fails (with error logged).

    Raises:
        No exceptions are raised — all errors are caught and logged.
        The caller (main.py) checks for None return to detect failures.

    CONCEPT — Why Return None Instead of Raising?
        In a pipeline, you often want the program to continue running
        even if one fetch fails. By returning None and logging the error,
        we let the caller decide how to handle the failure.
        This is called "graceful degradation."
    """

    logger.info("=" * 60)
    logger.info("Starting GNews API fetch")
    logger.info(f"Query: {GNEWS_QUERY}")
    logger.info(f"Max results: {GNEWS_MAX_RESULTS}")
    logger.info("=" * 60)

    # -------------------------------------------------------------------------
    # Step 1: Build the request parameters
    # -------------------------------------------------------------------------
    # The GNews API accepts parameters as URL query strings.
    # For example: ?q=artificial+intelligence&lang=en&country=us&max=10&apikey=xyz
    #
    # The 'requests' library handles URL encoding automatically when you
    # pass a dictionary to the 'params' argument.
    # -------------------------------------------------------------------------
    params = {
        "q":      GNEWS_QUERY,         # Search query
        "lang":   GNEWS_LANGUAGE,      # Language filter
        "country": GNEWS_COUNTRY,      # Country filter
        "max":    GNEWS_MAX_RESULTS,   # Number of articles (max 10 on free tier)
        "apikey": GNEWS_API_KEY,       # Your authentication key
    }

    # -------------------------------------------------------------------------
    # Step 2: Make the HTTP GET request with error handling
    # -------------------------------------------------------------------------
    # CONCEPT — try/except:
    #   Code inside 'try' runs normally.
    #   If an exception occurs, Python jumps to the matching 'except' block.
    #   Without try/except, any error would crash the entire program.
    # -------------------------------------------------------------------------
    try:
        logger.info(f"Sending GET request to {GNEWS_BASE_URL}")

        # requests.get() sends an HTTP GET request to the URL.
        # timeout=30 means: if the server doesn't respond in 30 seconds, give up.
        # Without a timeout, your program could hang forever waiting for a response.
        response = requests.get(GNEWS_BASE_URL, params=params, timeout=30)

        # -------------------------------------------------------------------------
        # Step 3: Check if the request was successful
        # -------------------------------------------------------------------------
        # HTTP Status Codes:
        #   200 OK           → Request succeeded
        #   401 Unauthorized → Invalid API key
        #   429 Too Many Req → Rate limit exceeded (too many calls)
        #   500 Server Error → GNews server has a problem
        #
        # raise_for_status() automatically raises an exception for 4xx and 5xx codes.
        # This saves us from writing: if response.status_code != 200: raise ...
        response.raise_for_status()

        logger.info(f"API response status: {response.status_code} OK")

    except requests.exceptions.Timeout:
        # This specific exception fires when the request takes longer than 'timeout'
        logger.error("GNews API request timed out after 30 seconds.")
        logger.error("Check your internet connection or try again later.")
        return None

    except requests.exceptions.ConnectionError:
        # This fires when we can't connect at all (e.g., no internet, DNS failure)
        logger.error("Could not connect to GNews API. Check your internet connection.")
        return None

    except requests.exceptions.HTTPError as e:
        # This fires when raise_for_status() triggers (4xx or 5xx response)
        # str(e) contains the status code and reason, e.g., "401 Client Error: Unauthorized"
        logger.error(f"HTTP error from GNews API: {str(e)}")
        logger.error("Common causes: Invalid API key (401) or rate limit exceeded (429).")
        return None

    except requests.exceptions.RequestException as e:
        # Catch-all for any other requests-related exception
        logger.error(f"Unexpected error during API request: {str(e)}")
        return None

    # -------------------------------------------------------------------------
    # Step 4: Parse the JSON response
    # -------------------------------------------------------------------------
    # response.json() converts the response body from a JSON string into a
    # Python dictionary. This is where your data actually lives.
    # -------------------------------------------------------------------------
    try:
        data = response.json()
    except ValueError as e:
        logger.error(f"Failed to parse API response as JSON: {str(e)}")
        return None

    # -------------------------------------------------------------------------
    # Step 5: Extract the list of articles
    # -------------------------------------------------------------------------
    # data["articles"] is a list of dictionaries.
    # If "articles" key doesn't exist (malformed response), we get an empty list.
    # -------------------------------------------------------------------------
    articles = data.get("articles", [])
    total_reported = data.get("totalArticles", 0)

    logger.info(f"GNews reports {total_reported} total matching articles")
    logger.info(f"Articles returned in this response: {len(articles)}")

    if not articles:
        logger.warning("No articles returned by the API.")
        logger.warning("Try broadening your search query in .env (GNEWS_QUERY).")
        return None

    # -------------------------------------------------------------------------
    # Step 6: Transform articles into structured records
    # -------------------------------------------------------------------------
    # CONCEPT — Data Transformation:
    #   Raw API data is often messy or nested.
    #   Here we "flatten" the nested JSON structure into a simple dictionary
    #   that maps directly to columns in our database table.
    #
    #   For example:
    #     Raw JSON:      article["source"]["name"]
    #     Transformed:   record["source"] = "TechCrunch"
    # -------------------------------------------------------------------------
    records = []  # This list will hold one dictionary per article

    for i, article in enumerate(articles):
        # Each 'article' is a Python dictionary from the JSON array
        logger.debug(f"Processing article {i + 1}: {article.get('title', 'No title')[:60]}...")

        # Build a flat dictionary matching our database schema.
        # NOTE: We do NOT include 'ingested_at' here.
        # The database model uses server_default=func.now(), which means
        # PostgreSQL sets ingested_at automatically when the row is inserted.
        # This is more reliable: the DB clock is authoritative, and all rows
        # in one batch get the exact same timestamp.
        record = {
            # Title of the news article
            "title": article.get("title", "").strip() or "No Title",

            # WEEK 3 CHANGE: source now represents the INGESTION SYSTEM ("GNews"),
            # not the individual publisher outlet (TechCrunch, Reuters, etc.).
            # This keeps the source column consistent with HN ("Hacker News") and
            # Reddit ("Reddit/MachineLearning") so the Source Analytics page
            # correctly groups by pipeline instead of by publisher.
            "source": "GNews",

            # Publisher outlet name stored in author.
            # GNews provides article["source"]["name"] = "TechCrunch" etc.
            # GNews rarely provides an actual journalist author name (it's usually
            # empty or missing). Using the publisher name here gives the dashboard
            # a meaningful value in the author/publisher column.
            "author": (article.get("source") or {}).get("name", "Unknown"),

            # Short description / subtitle of the article
            "description": article.get("description", "").strip() or None,

            # Publication timestamp from the API
            # GNews provides ISO 8601 format: "2026-06-24T10:00:00Z"
            # We parse it into a Python datetime object for proper DB storage
            "published_at": _parse_datetime(article.get("publishedAt")),

            # Unique URL of the article — this is our idempotency key
            # CONCEPT — Idempotency: if you run the pipeline twice,
            # the same article (same URL) won't be inserted twice.
            # We enforce this with a UNIQUE constraint in the database.
            "url": article.get("url", ""),

            # Category tag — always "AI" for this pipeline
            "category": GNEWS_CATEGORY,
        }

        # Skip articles with no URL — we can't enforce uniqueness without it
        if not record["url"]:
            logger.warning(f"Skipping article with no URL: {record['title']}")
            continue

        records.append(record)

    logger.info(f"Successfully transformed {len(records)} articles into records")

    if not records:
        logger.warning("All articles were skipped (missing URLs). Nothing to load.")
        return None

    # -------------------------------------------------------------------------
    # Step 7: Convert the list of dictionaries to a Pandas DataFrame
    # -------------------------------------------------------------------------
    # pd.DataFrame(records) takes a list of dicts and converts it to a table.
    # Each dictionary key becomes a column name.
    # Each dictionary is one row.
    #
    # Result:
    #   | title          | source     | author  | ... |
    #   |----------------|------------|---------|-----|
    #   | OpenAI GPT-5   | TechCrunch | Unknown | ... |
    #   | Gemini 2.0 Out | Wired      | Unknown | ... |
    # -------------------------------------------------------------------------
    df = pd.DataFrame(records)

    logger.info(f"DataFrame shape: {df.shape[0]} rows × {df.shape[1]} columns")
    logger.info(f"Columns: {list(df.columns)}")

    return df

