"""
Quick verification script for analytics/queries.py module.
Run: python scripts/verify_analytics.py
"""
from database.warehouse import create_db_engine
from analytics.queries import (
    get_total_article_count,
    get_todays_article_count,
    get_unique_source_count,
    get_last_updated_time,
    get_average_intelligence_score,
    get_articles_per_source,
    get_top_scored_articles,
    get_pipeline_health,
    get_keyword_frequency,
    search_articles,
)

print("Creating engine...")
engine = create_db_engine()

print()
print("=" * 55)
print("  ANALYTICS MODULE VERIFICATION")
print("=" * 55)

print(f"  Total articles:         {get_total_article_count(engine)}")
print(f"  Todays articles:        {get_todays_article_count(engine)}")
print(f"  Unique sources:         {get_unique_source_count(engine)}")
print(f"  Last updated:           {get_last_updated_time(engine)}")
print(f"  Avg intelligence score: {get_average_intelligence_score(engine)}")

print()
print("  --- Top Sources (top 5) ---")
df = get_articles_per_source(engine, top_n=5)
print(df.to_string(index=False))

print()
print("  --- Top Scored Articles (top 3) ---")
df = get_top_scored_articles(engine, limit=3)
for _, row in df.iterrows():
    score = row["intelligence_score"]
    title = str(row["title"])[:60]
    print(f"  [{score}] {title}...")

print()
print("  --- Keyword Frequency (top 5) ---")
df = get_keyword_frequency(engine, top_n=5)
print(df.to_string(index=False))

print()
print("  --- Pipeline Health ---")
health = get_pipeline_health(engine)
for k, v in health.items():
    print(f"  {k}: {v}")

print()
print("  --- Search Test (keyword: anthropic) ---")
df = search_articles(engine, keyword="anthropic", limit=3)
print(f"  Found {len(df)} results for 'anthropic'")

print()
print("=" * 55)
print("  ALL ANALYTICS FUNCTIONS: VERIFIED")
print("=" * 55)
