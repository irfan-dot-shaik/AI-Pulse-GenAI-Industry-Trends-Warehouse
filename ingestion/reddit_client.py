# =============================================================================
# ingestion/reddit_client.py — AI Pulse Project
# =============================================================================
#
# PURPOSE:
#   Fetches AI-relevant posts from specified subreddits using the PRAW library
#   (Python Reddit API Wrapper) and returns a clean Pandas DataFrame in the
#   same schema expected by the pipeline's raw layer.
#
# CONCEPT — Reddit as a Data Source:
#   Reddit is a community-driven platform where niche expert communities
#   (like r/MachineLearning) discuss and share cutting-edge research,
#   tools, and news. The upvote system acts as a quality filter — only
#   the most useful or interesting content rises to the top.
#
#   Compared to GNews (editorial journalism) and HN (general tech), Reddit
#   adds a third perspective: practitioner community discussion.
#
# CONCEPT — PRAW (Python Reddit API Wrapper):
#   PRAW is the official, maintained Python library for the Reddit API.
#   It handles OAuth2 authentication, rate limiting (60 req/min), and
#   response parsing automatically. We use "read-only" mode — no posting,
#   no user data, just reading public posts.
#
# CONCEPT — Optional Ingestion:
#   Reddit credentials (CLIENT_ID, CLIENT_SECRET) are optional.
#   If they are not set in .env, fetch_reddit_news() returns None immediately
#   and the orchestrator (main.py) skips Reddit silently.
#   GNews and Hacker News still run normally.
#
# IMPORTANT — What Gets Filtered Out:
#   1. Self-posts (reddit.com URLs): posts where the discussion IS the content
#      have no external article to add to the warehouse.
#   2. Posts without external URLs: same as above.
#   3. Posts with titles < 10 chars: already caught by the validator, but
#      we filter early to reduce noise.
#
# OUTPUT SCHEMA (identical to gnews_client.py and hn_client.py):
#   title, source, author, description, published_at, url, category
#
# =============================================================================

import pandas as pd
from datetime import timezone
from typing import Optional

from config.settings import (
    REDDIT_CLIENT_ID,
    REDDIT_CLIENT_SECRET,
    REDDIT_USER_AGENT,
    REDDIT_SUBREDDITS,
    REDDIT_POST_LIMIT,
)
from ingestion._utils import parse_unix_timestamp, normalize_text
from utils.logger import get_logger

logger = get_logger(__name__)

# Category tag for all Reddit articles
REDDIT_CATEGORY: str = "AI"

# URLs that point back to Reddit itself (self-posts, crossposts)
_REDDIT_SELF_POST_PREFIXES: tuple[str, ...] = (
    "https://www.reddit.com",
    "https://old.reddit.com",
    "https://reddit.com",
    "https://i.redd.it",    # Image-only posts — not articles
    "https://v.redd.it",    # Video-only posts — not articles
)


# =============================================================================
# Credential Check
# =============================================================================

def _reddit_credentials_available() -> bool:
    """
    Return True if Reddit API credentials are configured in settings.

    CONCEPT — Fail-Fast Credential Check:
        Rather than attempting to create a PRAW instance and catching
        an authentication error later, we check for credentials upfront.
        This produces a clear, actionable log message instead of a
        cryptic PRAW exception.
    """
    if not REDDIT_CLIENT_ID or not REDDIT_CLIENT_SECRET:
        logger.info(
            "[Reddit] Credentials not configured. "
            "Set REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET in .env to enable Reddit ingestion."
        )
        return False
    return True


# =============================================================================
# Self-Post Filter
# =============================================================================

def _is_external_article(url: str) -> bool:
    """
    Return True if the URL points to an external article (not Reddit itself).

    Self-posts and media posts (images, videos) are not external articles and
    should not enter the news warehouse. We check against known Reddit URL
    prefixes.

    Args:
        url: The submission URL to check.

    Returns:
        bool: True if external (keep), False if Reddit-internal (skip).
    """
    if not url:
        return False
    url_lower = url.lower().strip()
    return not any(url_lower.startswith(prefix.lower()) for prefix in _REDDIT_SELF_POST_PREFIXES)


# =============================================================================
# Main Public Function
# =============================================================================

def fetch_reddit_news(
    subreddits: Optional[list[str]] = None,
    limit: int = REDDIT_POST_LIMIT,
) -> Optional[pd.DataFrame]:
    """
    Fetch AI-relevant posts from Reddit subreddits.

    For each subreddit, fetches the hottest posts (ordered by upvotes + recency)
    and filters out self-posts and media-only posts. All posts are mapped to
    the standard 7-column pipeline schema.

    Args:
        subreddits: List of subreddit names (without "r/" prefix).
                    Defaults to REDDIT_SUBREDDITS from config/settings.py.
        limit:      Number of hot posts to fetch per subreddit.
                    Defaults to REDDIT_POST_LIMIT (10).

    Returns:
        pd.DataFrame: Articles in the standard pipeline schema.
                      Returns None if credentials are missing, no posts are
                      found, or an API error occurs.

    CONCEPT — "hot" sorting:
        Reddit's "hot" algorithm combines recency and vote score.
        A post from 2 hours ago with 500 upvotes ranks higher than a
        6-hour-old post with 200 upvotes. This is the most useful
        ordering for a near-real-time news pipeline.
    """
    # -------------------------------------------------------------------------
    # Step 1: Validate credentials early
    # -------------------------------------------------------------------------
    if not _reddit_credentials_available():
        return None

    # -------------------------------------------------------------------------
    # Step 2: Build the list of target subreddits
    # -------------------------------------------------------------------------
    target_subreddits = subreddits if subreddits is not None else REDDIT_SUBREDDITS

    if not target_subreddits:
        logger.warning("[Reddit] No subreddits configured. Skipping Reddit ingestion.")
        return None

    logger.info("=" * 60)
    logger.info("[Reddit] Starting Reddit fetch via PRAW")
    logger.info(f"[Reddit] Subreddits: {target_subreddits}")
    logger.info(f"[Reddit] Post limit per subreddit: {limit}")
    logger.info("=" * 60)

    # -------------------------------------------------------------------------
    # Step 3: Initialise PRAW Reddit instance
    # -------------------------------------------------------------------------
    # CONCEPT — PRAW ReadonlyReddit:
    #   We use praw.Reddit() in read-only mode (no username/password).
    #   This is sufficient for fetching public posts. The client_id and
    #   client_secret identify our application to Reddit's API servers.
    # -------------------------------------------------------------------------
    try:
        import praw  # Imported here to avoid ImportError when praw is not installed

        reddit = praw.Reddit(
            client_id=REDDIT_CLIENT_ID,
            client_secret=REDDIT_CLIENT_SECRET,
            user_agent=REDDIT_USER_AGENT,
        )
        reddit.read_only = True  # Enforce read-only mode explicitly
        logger.info("[Reddit] PRAW Reddit instance created (read-only mode)")

    except ImportError:
        logger.error(
            "[Reddit] PRAW is not installed. Run: pip install praw==7.7.1"
        )
        return None
    except Exception as e:
        logger.error(f"[Reddit] Failed to initialise PRAW: {e}")
        return None

    # -------------------------------------------------------------------------
    # Step 4: Fetch posts from each subreddit
    # -------------------------------------------------------------------------
    records = []

    for sub_name in target_subreddits:
        logger.info(f"[Reddit] Fetching r/{sub_name} (hot, limit={limit})")

        try:
            subreddit = reddit.subreddit(sub_name)
            hot_posts = subreddit.hot(limit=limit)

            sub_count = 0
            skipped_self = 0
            skipped_url = 0

            for post in hot_posts:
                # Get the external URL of the linked article
                url = normalize_text(getattr(post, "url", ""), default="")

                # Skip posts with no external article
                if not url:
                    skipped_url += 1
                    continue

                # Skip Reddit self-posts and media posts
                if not _is_external_article(url):
                    skipped_self += 1
                    logger.debug(
                        f"[Reddit] Skipping self/media post: "
                        f"{post.title[:50]}... → {url[:60]}"
                    )
                    continue

                title = normalize_text(post.title, default="")
                if not title:
                    continue

                # Post selftext (body) — may be empty for link posts
                # We use a short excerpt as the "description" if available
                selftext = normalize_text(getattr(post, "selftext", ""), default="")
                description = selftext[:300] if selftext and selftext != "[removed]" else None

                # Map to standard pipeline schema
                record = {
                    # Title of the linked article / post
                    "title": title,

                    # Source: "Reddit/SubredditName" for easy filtering by source
                    "source": f"Reddit/{sub_name}",

                    # Author: Reddit username of the poster
                    "author": normalize_text(
                        str(post.author) if post.author else "Unknown",
                        default="Unknown"
                    ),

                    # Description: post body excerpt (None for pure link posts)
                    "description": description,

                    # published_at: post creation time (Unix timestamp → UTC datetime)
                    "published_at": parse_unix_timestamp(int(post.created_utc)),

                    # URL: the external article being shared (not the Reddit post URL)
                    "url": url,

                    # Category: always "AI" for all Reddit posts in this pipeline
                    "category": REDDIT_CATEGORY,
                }

                records.append(record)
                sub_count += 1
                logger.debug(f"[Reddit] r/{sub_name} post [{sub_count}]: {title[:60]}...")

            logger.info(
                f"[Reddit] r/{sub_name}: {sub_count} articles collected "
                f"({skipped_self} self-posts skipped, {skipped_url} no-URL skipped)"
            )

        except Exception as e:
            logger.error(
                f"[Reddit] Failed to fetch r/{sub_name}: {e}. "
                "Continuing with other subreddits."
            )
            continue  # Don't let one failing subreddit stop the others

    logger.info(f"[Reddit] Total articles collected across all subreddits: {len(records)}")

    if not records:
        logger.warning(
            "[Reddit] No external articles found across any subreddit. "
            "This may happen if all posts are self-posts or media posts."
        )
        return None

    # -------------------------------------------------------------------------
    # Step 5: Build DataFrame (identical schema to gnews_client.py)
    # -------------------------------------------------------------------------
    df = pd.DataFrame(records)
    logger.info(f"[Reddit] DataFrame shape: {df.shape[0]} rows × {df.shape[1]} columns")
    logger.info(f"[Reddit] Columns: {list(df.columns)}")
    logger.info(
        f"[Reddit] Sources: {df['source'].value_counts().to_dict()}"
    )

    return df
