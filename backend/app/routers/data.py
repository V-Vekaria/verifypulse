"""
VerifyPulse API Router — Data
Articles, sources, stats, fetch, and report endpoints.
"""

from fastapi import APIRouter, Query
from fastapi.responses import PlainTextResponse
from datetime import datetime

from app.services.rss_fetcher import fetch_all_rss
from app.services.gdelt_client import fetch_gdelt_by_regions
from app.services.database import (
    insert_articles,
    get_articles,
    get_article_count,
    get_source_stats,
    get_unique_source_count,
    get_last_fetch,
    log_fetch,
)
from app.services.dedup import deduplicate_articles, get_existing_titles_from_db
from app.services.clustering import cluster_articles
from app.services.confidence import score_all_clusters
from app.services.report_generator import generate_daily_report

router = APIRouter(prefix="/api", tags=["data"])


@router.post("/fetch")
def trigger_fetch():
    """Manually trigger a news fetch from all sources."""
    rss_articles = fetch_all_rss()
    gdelt_articles = fetch_gdelt_by_regions()
    all_articles = rss_articles + gdelt_articles

    existing_titles = get_existing_titles_from_db()
    unique, duplicates = deduplicate_articles(all_articles, existing_titles)

    result = {"new": 0, "duplicate": 0}
    if unique:
        article_dicts = [a.model_dump() for a in unique]
        result = insert_articles(article_dicts)

    total_dups = len(duplicates) + result["duplicate"]
    log_fetch(
        rss_count=len(rss_articles),
        gdelt_count=len(gdelt_articles),
        new=result["new"],
        duplicate=total_dups,
    )

    return {
        "status": "success",
        "rss_count": len(rss_articles),
        "gdelt_count": len(gdelt_articles),
        "new_articles": result["new"],
        "duplicates_filtered": total_dups,
        "total_in_database": get_article_count(),
        "fetched_at": datetime.now().isoformat(),
    }


@router.get("/articles")
def list_articles(
    region: str | None = Query(None),
    lang: str | None = Query(None, description="Filter by language: en, hi"),
    limit: int = Query(50),
    offset: int = Query(0),
    hours: int | None = Query(None),
):
    """Get raw articles from database with optional filters."""
    articles = get_articles(region=region, limit=limit, offset=offset, hours=hours)

    # Filter by language if requested
    if lang:
        articles = [a for a in articles if a.get("language", "en") == lang]

    total = get_article_count(region=region)

    return {
        "count": len(articles),
        "total": total,
        "region": region or "all",
        "lang": lang or "all",
        "articles": articles,
    }


@router.get("/sources")
def list_sources():
    """All configured sources with credibility scores and article counts."""
    sources = get_source_stats()
    return {"count": len(sources), "sources": sources}


@router.get("/stats")
def get_stats():
    """Dashboard stats — system overview with per-region counts."""
    last = get_last_fetch()
    return {
        "total_articles": get_article_count(),
        "active_sources": get_unique_source_count(),
        "regions": {
            "global": get_article_count("global"),
            "india": get_article_count("india"),
            "east_asia": get_article_count("east_asia"),
            "americas": get_article_count("americas"),
        },
        "last_fetch": last if last else None,
    }


@router.get("/reports/daily")
def get_daily_report(format: str = Query("json", description="Response format: json or markdown")):
    """
    **Daily misinformation report** — summarises today's low-confidence stories.

    Uses Claude API to generate a natural language summary.
    Falls back to basic markdown if ANTHROPIC_API_KEY is not set.

    Use ?format=markdown to get the raw markdown text.
    """
    clusters = cluster_articles(hours=24)
    scored = score_all_clusters(clusters)
    report = generate_daily_report(scored)

    if format == "markdown":
        return PlainTextResponse(
            content=report["markdown"],
            media_type="text/markdown",
        )

    return report