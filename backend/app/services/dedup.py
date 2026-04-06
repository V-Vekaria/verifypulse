"""
VerifyPulse Deduplication Service
Catches duplicate articles even when URLs differ but titles are similar.
Uses difflib for fast string similarity — no heavy ML needed.
"""

from difflib import SequenceMatcher
from typing import Optional

from app.models import Article


# ─── SIMILARITY THRESHOLD ───────────────────────────────────────
# Two titles with >= 75% similarity are considered duplicates.
# This catches "India PM visits Japan" vs "Indian PM visits Japan for summit"
# but won't merge "India PM visits Japan" with "Japan PM visits India"
TITLE_SIMILARITY_THRESHOLD = 0.75


def calculate_title_similarity(title_a: str, title_b: str) -> float:
    """
    Calculate similarity ratio between two article titles.

    Args:
        title_a: First title
        title_b: Second title

    Returns:
        Float between 0.0 (completely different) and 1.0 (identical)
    """
    # Normalize: lowercase and strip extra whitespace
    a = " ".join(title_a.lower().split())
    b = " ".join(title_b.lower().split())

    return SequenceMatcher(None, a, b).ratio()


def deduplicate_articles(
    new_articles: list[Article],
    existing_titles: Optional[list[str]] = None,
) -> tuple[list[Article], list[Article]]:
    """
    Remove duplicate articles from a batch.

    Checks for duplicates in two ways:
    1. Within the batch itself (e.g., same story from RSS and GDELT)
    2. Against existing titles from the database (optional)

    Args:
        new_articles: List of freshly fetched articles
        existing_titles: Titles already in the database (optional)

    Returns:
        Tuple of (unique_articles, duplicate_articles)
    """
    unique = []
    duplicates = []
    seen_titles: list[str] = list(existing_titles or [])
    seen_urls: set[str] = set()

    for article in new_articles:
        # Check 1: Exact URL match
        if article.url in seen_urls:
            duplicates.append(article)
            continue

        # Check 2: Title similarity against already-seen titles
        is_dup = False
        for existing_title in seen_titles:
            similarity = calculate_title_similarity(article.title, existing_title)
            if similarity >= TITLE_SIMILARITY_THRESHOLD:
                is_dup = True
                break

        if is_dup:
            duplicates.append(article)
        else:
            unique.append(article)
            seen_titles.append(article.title)
            seen_urls.add(article.url)

    return unique, duplicates


def get_existing_titles_from_db() -> list[str]:
    """
    Fetch recent article titles from database for dedup comparison.
    Only checks last 24 hours to keep the comparison fast.
    """
    from app.services.database import get_db

    with get_db() as conn:
        rows = conn.execute("""
            SELECT title FROM articles
            WHERE fetched_at >= datetime('now', '-24 hours')
        """).fetchall()
        return [row["title"] for row in rows]
