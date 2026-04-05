"""
GDELT API Client
Fetches articles from the GDELT Project's free global news API.
GDELT monitors news in 100+ languages and updates every 15 minutes.
"""

import requests
import hashlib
from datetime import datetime
from typing import Optional

from app.config import GDELT_DOC_API, GDELT_DEFAULT_PARAMS, REGION_QUERIES
from app.models import Article


def _generate_article_id(url: str) -> str:
    """Create a unique ID from the article URL."""
    return hashlib.md5(url.encode()).hexdigest()[:12]


def _detect_region(title: str, url: str) -> str:
    """Simple keyword-based region detection."""
    text = (title + " " + url).lower()

    india_keywords = ["india", "delhi", "mumbai", "modi", "ndtv", "hindu"]
    asia_keywords = ["china", "japan", "korea", "tokyo", "beijing", "shanghai"]
    americas_keywords = ["us ", "america", "congress", "washington", "biden", "trump"]

    for kw in india_keywords:
        if kw in text:
            return "india"
    for kw in asia_keywords:
        if kw in text:
            return "east_asia"
    for kw in americas_keywords:
        if kw in text:
            return "americas"

    return "global"


def fetch_gdelt(
    query: str = "", region: Optional[str] = None, max_records: int = 50
) -> list[Article]:
    """
    Fetch articles from GDELT's DOC API.

    Args:
        query: Search query (optional)
        region: Filter by region key (optional)
        max_records: Maximum articles to return

    Returns:
        List of Article objects
    """
    print(f"\n🌍 Fetching GDELT articles...")

    # Build query
    search_query = query
    if region and region in REGION_QUERIES and REGION_QUERIES[region]:
        if search_query:
            search_query = f"({search_query}) AND ({REGION_QUERIES[region]})"
        else:
            search_query = REGION_QUERIES[region]

    # If no query at all, use a broad search
    if not search_query:
        search_query = "breaking news world"

    params = {
        **GDELT_DEFAULT_PARAMS,
        "query": search_query,
        "maxrecords": max_records,
    }

    articles = []

    try:
        response = requests.get(GDELT_DOC_API, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()

        raw_articles = data.get("articles", [])

        for item in raw_articles:
            url = item.get("url", "")
            title = item.get("title", "")

            if not url or not title:
                continue

            # GDELT doesn't provide a single source credibility —
            # we assign a base score of 65 (moderate) since GDELT
            # aggregates from many sources of varying quality
            article = Article(
                id=_generate_article_id(url),
                title=title,
                url=url,
                source_id="gdelt_" + item.get("domain", "unknown").replace(".", "_"),
                source_name=item.get("domain", "GDELT Source"),
                published_at=_parse_gdelt_date(item.get("seendate")),
                summary=None,  # GDELT doc API doesn't always include summaries
                region=_detect_region(title, url),
                credibility_score=65,
            )
            articles.append(article)

        print(f"  ✓ GDELT: {len(articles)} articles")

    except requests.exceptions.Timeout:
        print("  ✗ GDELT: Request timed out (15s)")
    except requests.exceptions.RequestException as e:
        print(f"  ✗ GDELT request failed: {e}")
    except (ValueError, KeyError) as e:
        print(f"  ✗ GDELT parse error: {e}")

    return articles


def _parse_gdelt_date(date_str: Optional[str]) -> Optional[datetime]:
    """Parse GDELT's date format (YYYYMMDDHHmmss)."""
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str[:14], "%Y%m%d%H%M%S")
    except (ValueError, TypeError):
        return None


def fetch_gdelt_by_regions() -> list[Article]:
    """
    Fetch articles for all configured regions.

    Returns:
        Combined list of articles across all regions.
    """
    all_articles = []

    for region_key in ["global", "india", "east_asia", "americas"]:
        articles = fetch_gdelt(region=region_key, max_records=25)
        all_articles.extend(articles)

    print(f"📊 Total GDELT articles: {len(all_articles)}")
    return all_articles
