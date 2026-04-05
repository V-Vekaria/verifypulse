"""
RSS Feed Parser Service
Fetches and parses articles from configured RSS news sources.
"""

import feedparser
import hashlib
from datetime import datetime
from dateutil import parser as date_parser
from typing import Optional

from app.config import RSS_SOURCES
from app.models import Article


def _generate_article_id(url: str) -> str:
    """Create a unique ID from the article URL."""
    return hashlib.md5(url.encode()).hexdigest()[:12]


def _parse_date(date_str: Optional[str]) -> Optional[datetime]:
    """Safely parse various date formats from RSS feeds."""
    if not date_str:
        return None
    try:
        return date_parser.parse(date_str)
    except (ValueError, TypeError):
        return None


def _clean_summary(summary: Optional[str]) -> Optional[str]:
    """Remove HTML tags from summary text."""
    if not summary:
        return None
    import re

    clean = re.sub(r"<[^>]+>", "", summary)
    clean = clean.strip()
    # Truncate to 500 chars
    return clean[:500] if len(clean) > 500 else clean


def fetch_single_source(source: dict) -> list[Article]:
    """
    Fetch articles from a single RSS source.

    Args:
        source: Source config dict from RSS_SOURCES

    Returns:
        List of Article objects
    """
    articles = []

    try:
        feed = feedparser.parse(source["url"])

        if feed.bozo and not feed.entries:
            print(f"  ⚠ Feed error for {source['name']}: {feed.bozo_exception}")
            return articles

        for entry in feed.entries[:20]:  # max 20 per source
            url = entry.get("link", "")
            if not url:
                continue

            article = Article(
                id=_generate_article_id(url),
                title=entry.get("title", "Untitled"),
                url=url,
                source_id=source["id"],
                source_name=source["name"],
                published_at=_parse_date(
                    entry.get("published") or entry.get("updated")
                ),
                summary=_clean_summary(
                    entry.get("summary") or entry.get("description")
                ),
                region=source["region"],
                credibility_score=source["credibility_score"],
            )
            articles.append(article)

        print(f"  ✓ {source['name']}: {len(articles)} articles")

    except Exception as e:
        print(f"  ✗ {source['name']} failed: {e}")

    return articles


def fetch_all_rss() -> list[Article]:
    """
    Fetch articles from ALL configured RSS sources.

    Returns:
        Combined list of articles from all sources.
    """
    print("\n📡 Fetching RSS feeds...")
    all_articles = []

    for source in RSS_SOURCES:
        articles = fetch_single_source(source)
        all_articles.extend(articles)

    print(f"📊 Total RSS articles: {len(all_articles)}")
    return all_articles
