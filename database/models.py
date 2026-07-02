# =============================================================================
# database/models.py — AI Pulse Project
# =============================================================================
#
# PURPOSE:
#   Defines the database table schema using SQLAlchemy's ORM (Object Relational
#   Mapper). Instead of writing raw SQL like:
#     CREATE TABLE raw_ai_news (id SERIAL PRIMARY KEY, title TEXT, ...)
#   we define a Python class that SQLAlchemy converts to SQL automatically.
#
# CONCEPT — What Is an ORM?
#   An ORM (Object Relational Mapper) is a layer between Python and SQL.
#   It lets you work with database tables as Python classes (objects).
#
#   Without ORM (raw SQL):
#     cursor.execute("INSERT INTO raw_ai_news (title) VALUES (%s)", ("AI News",))
#
#   With ORM (SQLAlchemy):
#     article = RawAiNews(title="AI News")
#     session.add(article)
#     session.commit()
#
#   Benefits of ORM:
#     - No SQL injection risk (parameters are sanitized automatically)
#     - Easier to read and maintain
#     - Database-agnostic (same code works with PostgreSQL, SQLite, MySQL)
#     - Auto-migration support (Week 2+)
#
# CONCEPT — What Is DeclarativeBase?
#   SQLAlchemy uses a "Base" class from which all table classes inherit.
#   SQLAlchemy uses this Base to know which classes represent database tables.
#   When we call Base.metadata.create_all(engine), it creates ALL tables
#   defined by classes that inherit from Base.
#
# =============================================================================

from datetime import datetime         # For typed datetime columns
from typing import Optional           # For nullable (optional) columns

from sqlalchemy import (
    Integer,       # SQL INTEGER type → Python int
    Text,          # SQL TEXT type → Python str (unlimited length)
    DateTime,      # SQL TIMESTAMP type → Python datetime
    String,        # SQL VARCHAR type → Python str (fixed max length)
    UniqueConstraint,  # Enforce uniqueness across one or more columns
)
from sqlalchemy.orm import (
    DeclarativeBase,   # Base class for all ORM models
    Mapped,            # Type annotation for ORM columns
    mapped_column,     # Defines a column with its SQL type and constraints
)
from sqlalchemy.sql import func       # SQL functions like func.now()


# =============================================================================
# Base Class
# =============================================================================
# All ORM model classes must inherit from this Base.
# SQLAlchemy uses Base.metadata to keep track of all table definitions.
# =============================================================================

class Base(DeclarativeBase):
    """Base class for all SQLAlchemy ORM models in this project."""
    pass


# =============================================================================
# RawAiNews — Maps to the "raw_ai_news" PostgreSQL table
# =============================================================================
#
# DATA ENGINEERING CONVENTION — Naming Layers:
#   raw_    → Data exactly as it came from the source (no transformations)
#   stg_    → Staging: lightly cleaned (Week 2)
#   int_    → Intermediate: business logic applied (Week 2/3)
#   fct_    → Fact tables: final analytical tables (Week 2/3)
#
# We're in the raw_ layer. This table stores articles EXACTLY as returned
# by the GNews API, with minimal transformation (just flattening the JSON).
#
# =============================================================================

class RawAiNews(Base):
    """
    ORM model representing the raw_ai_news PostgreSQL table.

    Each instance of this class represents one row in the table
    (one news article ingested from GNews API).

    TABLE: raw_ai_news
    """

    # __tablename__ tells SQLAlchemy what this class maps to in PostgreSQL
    __tablename__ = "raw_ai_news"

    # -------------------------------------------------------------------------
    # Columns
    # -------------------------------------------------------------------------
    # Syntax: column_name: Mapped[type] = mapped_column(SQL_TYPE, options...)
    #
    # Mapped[int]           → required integer column
    # Mapped[Optional[str]] → nullable string column (can be NULL in DB)
    # -------------------------------------------------------------------------

    # PRIMARY KEY: A unique identifier for each row.
    # SERIAL in PostgreSQL = auto-incrementing integer (1, 2, 3, ...).
    # init=False means we never pass this when creating a RawAiNews object;
    # PostgreSQL assigns it automatically.
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Title of the news article — required, cannot be NULL
    title: Mapped[str] = mapped_column(Text, nullable=False)

    # Name of the news source (e.g., "TechCrunch", "Wired")
    source: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Author name — GNews rarely provides this, so defaults to "Unknown"
    author: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Short description / subtitle of the article
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # When the article was PUBLISHED (from the API) — timezone-aware
    # timezone=True stores as TIMESTAMP WITH TIME ZONE in PostgreSQL
    published_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Canonical URL of the article
    # The UNIQUE constraint is enforced via __table_args__ below (named constraint).
    # We do NOT set unique=True here to avoid SQLAlchemy generating a duplicate index.
    # CONCEPT — Idempotency: if you run the pipeline twice, the same article
    # (same URL) won't be inserted twice. The named constraint in __table_args__
    # is the single, authoritative enforcement point.
    url: Mapped[str] = mapped_column(Text, nullable=False)

    # Topic category — "AI" for all articles in Week 1
    # Using String(50) instead of Text because categories are short and fixed
    category: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, default="AI")

    # When WE loaded this record into the warehouse.
    # server_default=func.now() means PostgreSQL itself sets this timestamp.
    # IMPORTANT: We do NOT pass ingested_at from Python — we let the database
    # set it automatically. This is more reliable because:
    #   1. The DB clock is authoritative (not affected by Python timezone issues)
    #   2. All rows in the same batch get the exact same timestamp
    # The ingestion/gnews_client.py should NOT include ingested_at in the DataFrame.
    ingested_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=True,
    )

    # -------------------------------------------------------------------------
    # Table-Level Constraints
    # -------------------------------------------------------------------------
    # __table_args__ allows adding constraints that apply to the whole table,
    # not just a single column. Here we add a named UNIQUE constraint on 'url'.
    #
    # WHY name the constraint?
    #   Named constraints can be referenced in error messages and ALTER TABLE
    #   statements. "uq_raw_ai_news_url" tells you exactly what the constraint is.
    # -------------------------------------------------------------------------
    __table_args__ = (
        UniqueConstraint("url", name="uq_raw_ai_news_url"),
    )

    def __repr__(self) -> str:
        """
        String representation of the object — useful for debugging.
        When you print a RawAiNews object, you'll see something like:
            <RawAiNews id=1 title='OpenAI releases GPT-5' source='TechCrunch'>
        """
        return (
            f"<RawAiNews "
            f"id={self.id} "
            f"title='{self.title[:40]}...' "
            f"source='{self.source}'"
            f">"
        )


# =============================================================================
# StagingAiNews — Maps to the "stg_ai_news" PostgreSQL table
# =============================================================================
#
# WEEK 2 ADDITION — Staging Layer
#
# DATA ENGINEERING CONVENTION — Layer Naming:
#   raw_  → exactly as received from source  (raw_ai_news  — Week 1)
#   stg_  → cleaned, validated, enriched     (stg_ai_news  — Week 2)
#   fct_  → fact tables for analytics        (Week 3+)
#
# WHY A SEPARATE STAGING TABLE?
#   The raw layer must NEVER be modified — it is the audit trail.
#   The staging layer is our "working copy":
#     - Normalized text (stripped, title-cased)
#     - Validated (only complete records)
#     - Enriched (intelligence_score added)
#
#   If we discover a bug in our cleaning logic later, we can:
#     1. Fix the processing code
#     2. Re-run processing from raw_ai_news
#     3. Rebuild stg_ai_news cleanly
#
#   This is called "raw layer as source of truth" — a Data Engineering best practice.
#
# ADDITIONAL COLUMNS vs. raw_ai_news:
#   intelligence_score  → 0–100 score from scorer.py
#   score_category      → "Hot Trend" / "High Impact" / "Trending" / "Normal"
#   is_valid            → True for all rows (invalid rows never reach staging)
#   validation_notes    → "" for valid rows; rejection reason for invalid ones
#   keywords_found      → comma-separated list of matched AI keywords
#   processed_at        → when this row was processed (set by PostgreSQL)
#
# =============================================================================

class StagingAiNews(Base):
    """
    ORM model representing the stg_ai_news PostgreSQL staging table.

    Contains cleaned, validated, and scored versions of articles from raw_ai_news.
    This is the table queried by the analytics module and the Streamlit dashboard.

    TABLE: stg_ai_news
    """

    __tablename__ = "stg_ai_news"

    # -------------------------------------------------------------------------
    # Core Columns (same as raw_ai_news — cleaned versions)
    # -------------------------------------------------------------------------

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )

    # Cleaned title (whitespace stripped)
    title: Mapped[str] = mapped_column(Text, nullable=False)

    # Normalized source name (title-cased)
    source: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Normalized author ("Unknown" if not provided)
    author: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Cleaned and truncated description (max 1000 chars)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Publication timestamp (timezone-aware)
    published_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # URL — our idempotency key (same UNIQUE constraint as raw layer)
    # UNIQUE enforced via __table_args__ below
    url: Mapped[str] = mapped_column(Text, nullable=False)

    # Normalized category (always uppercase: "AI")
    category: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True, default="AI"
    )

    # When the raw article was ingested (carried over from raw_ai_news)
    ingested_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # -------------------------------------------------------------------------
    # Week 2 Enrichment Columns
    # -------------------------------------------------------------------------

    # AI News Intelligence Score (0–100)
    # Computed by processing/scorer.py using 4 transparent rules
    intelligence_score: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, default=0
    )

    # Human-readable score category based on intelligence_score
    # Values: "Hot Trend" / "High Impact" / "Trending" / "Normal"
    score_category: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True, default="Normal"
    )

    # Whether this article passed all validation rules (always True for staged rows)
    is_valid: Mapped[Optional[bool]] = mapped_column(
        # Using Integer(1) as boolean for broader DB compatibility
        Integer, nullable=True, default=1
    )

    # Rejection reason if invalid (empty string for valid rows)
    validation_notes: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, default=""
    )

    # Comma-separated AI keywords found in title + description
    # Example: "openai, gpt, llm"
    keywords_found: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, default=""
    )

    # When THIS row was processed (set by PostgreSQL, not Python)
    # server_default=func.now() means DB sets this automatically
    processed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=True,
    )

    # -------------------------------------------------------------------------
    # Table-Level Constraints
    # -------------------------------------------------------------------------
    __table_args__ = (
        UniqueConstraint("url", name="uq_stg_ai_news_url"),
    )

    def __repr__(self) -> str:
        """
        String representation for debugging.
        Example:
            <StagingAiNews id=1 score=87 title='OpenAI releases GPT-5...'>
        """
        return (
            f"<StagingAiNews "
            f"id={self.id} "
            f"score={self.intelligence_score} "
            f"category='{self.score_category}' "
            f"title='{self.title[:40]}...'"
            f">"
        )
