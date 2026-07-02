# =============================================================================
# processing/__init__.py — AI Pulse Project
# =============================================================================
#
# PURPOSE:
#   Makes 'processing' a Python package so you can import from it:
#     from processing.validator import validate_articles
#     from processing.scorer   import score_articles
#     from processing.transformer import transform_articles
#
# CONCEPT — Python Packages:
#   Any folder containing an __init__.py file is treated as a "package"
#   by Python. Without this file, Python cannot find the modules inside.
#
# WEEK 2 — Processing Layer:
#   This package is responsible for taking raw articles from the GNews API
#   and preparing them for the staging layer (stg_ai_news table).
#
#   Data flow:
#     raw DataFrame
#       → validator.py  (remove incomplete records)
#       → transformer.py (clean + normalize text)
#       → scorer.py     (compute AI Intelligence Score 0-100)
#       → stg_ai_news   (PostgreSQL staging table)
#
# =============================================================================
