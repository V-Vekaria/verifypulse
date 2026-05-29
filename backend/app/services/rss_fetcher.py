"""
RSS Feed Parser Service
Fetches and parses articles from configured RSS news sources.
Day 5: added language detection per article.
"""

import socket
import feedparser
import hashlib
import re
from datetime import datetime
from dateutil import parser as date_parser
from typing import Optional

# feedparser has no built-in timeout — set a global socket timeout for feed fetches
_FEED_TIMEOUT = 10  # seconds

from app.config import RSS_SOURCES
from app.models import Article


def _generate_article_id(url: str) -> str:
    return hashlib.md5(url.encode()).hexdigest()[:12]


def _parse_date(date_str: Optional[str]) -> Optional[datetime]:
    if not date_str:
        return None
    try:
        return date_parser.parse(date_str)
    except (ValueError, TypeError):
        return None


def _clean_summary(summary: Optional[str]) -> Optional[str]:
    if not summary:
        return None
    clean = re.sub(r"<[^>]+>", "", summary)
    clean = clean.strip()
    return clean[:500] if len(clean) > 500 else clean


def _detect_language(text: str) -> str:
    """
    Lightweight language detection — checks for Hindi Unicode range.
    Returns 'hi' for Hindi, 'en' for everything else.
    No external dependency needed for basic Hindi detection.
    """
    if not text:
        return "en"
    # Devanagari Unicode block: U+0900–U+097F
    hindi_chars = sum(1 for c in text if "\u0900" <= c <= "\u097F")
    # If >10% of chars are Devanagari, classify as Hindi
    if len(text) > 0 and hindi_chars / len(text) > 0.1:
        return "hi"
    return "en"


def fetch_single_source(source: dict) -> list[Article]:
    """Fetch articles from a single RSS source."""
    articles = []
    # Use source-level language if defined, otherwise auto-detect
    source_language = source.get("language", None)

    try:
        old_timeout = socket.getdefaulttimeout()
        socket.setdefaulttimeout(_FEED_TIMEOUT)
        try:
            feed = feedparser.parse(source["url"])
        finally:
            socket.setdefaulttimeout(old_timeout)

        if feed.bozo and not feed.entries:
            print(f"  [WARN] Feed error for {source['name']}: {feed.bozo_exception}")
            return articles

        for entry in feed.entries[:20]:
            url = entry.get("link", "")
            if not url:
                continue

            title = entry.get("title", "Untitled")
            summary = _clean_summary(
                entry.get("summary") or entry.get("description")
            )

            # Detect language from title if source doesn't declare one
            lang = source_language or _detect_language(title)

            article = Article(
                id=_generate_article_id(url),
                title=title,
                url=url,
                source_id=source["id"],
                source_name=source["name"],
                published_at=_parse_date(
                    entry.get("published") or entry.get("updated")
                ),
                summary=summary,
                region=source["region"],
                credibility_score=source["credibility_score"],
                language=lang,
            )
            articles.append(article)

        print(f"  [OK] {source['name']}: {len(articles)} articles")

    except Exception as e:
        print(f"  [ERR] {source['name']} failed: {e}")

    return articles


def fetch_all_rss() -> list[Article]:
    """Fetch articles from ALL configured RSS sources."""
    print("\n[RSS] Fetching RSS feeds...")
    all_articles = []

    for source in RSS_SOURCES:
        articles = fetch_single_source(source)
        all_articles.extend(articles)

    print(f"📊 Total RSS articles: {len(all_articles)}")
    return all_articles