"""
VerifyPulse — Main Application
Real-time news verification dashboard.

Run with: uvicorn app.main:app --reload
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime

from app.services.rss_fetcher import fetch_all_rss
from app.services.gdelt_client import fetch_gdelt_by_regions
from app.services.database import (
    init_database,
    insert_articles,
    get_articles,
    get_article_count,
    get_source_stats,
    get_unique_source_count,
    get_last_fetch,
    log_fetch,
)
from app.services.dedup import deduplicate_articles, get_existing_titles_from_db
from app.services.scheduler import start_scheduler, stop_scheduler
from app.models import HealthResponse

# ─── APP SETUP ──────────────────────────────────────────────────
app = FastAPI(
    title="VerifyPulse API",
    description="Real-time news verification and confidence scoring",
    version="0.2.0",
)

# Allow frontend to connect (Day 5)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── ROUTES ─────────────────────────────────────────────────────
@app.get("/", tags=["health"])
def root():
    """Root endpoint — confirms the API is running."""
    return {
        "app": "VerifyPulse",
        "version": "0.2.0",
        "status": "running",
        "docs": "/docs",
        "database": "SQLite (persistent)",
    }


@app.get("/api/health", response_model=HealthResponse, tags=["health"])
def health_check():
    """Health check with stats from database."""
    last = get_last_fetch()
    return HealthResponse(
        status="ok",
        total_articles=get_article_count(),
        total_sources=get_unique_source_count(),
        last_fetch=last["fetched_at"] if last else None,
    )


@app.post("/api/fetch", tags=["data"])
def trigger_fetch():
    """
    Manually trigger a news fetch from all sources.
    Articles are deduplicated and stored in SQLite.
    The scheduler also runs this automatically every 15 minutes.
    """
    # Fetch from all sources
    rss_articles = fetch_all_rss()
    gdelt_articles = fetch_gdelt_by_regions()
    all_articles = rss_articles + gdelt_articles

    # Deduplicate against existing database
    existing_titles = get_existing_titles_from_db()
    unique, duplicates = deduplicate_articles(all_articles, existing_titles)

    # Store in database
    result = {"new": 0, "duplicate": 0}
    if unique:
        article_dicts = [a.model_dump() for a in unique]
        result = insert_articles(article_dicts)

    # Log the fetch
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


@app.get("/api/articles", tags=["data"])
def list_articles(
    region: str | None = None,
    limit: int = 50,
    offset: int = 0,
    hours: int | None = None,
):
    """
    Get articles from database with optional filters.

    - **region**: Filter by region (global, india, east_asia, americas)
    - **limit**: Max articles to return (default 50)
    - **offset**: Pagination offset
    - **hours**: Only articles from the last N hours
    """
    articles = get_articles(region=region, limit=limit, offset=offset, hours=hours)
    total = get_article_count(region=region)

    return {
        "count": len(articles),
        "total": total,
        "region": region or "all",
        "articles": articles,
    }


@app.get("/api/sources", tags=["data"])
def list_sources():
    """
    Get all configured sources with credibility scores and article counts.
    Shows which sources are contributing data.
    """
    sources = get_source_stats()
    return {
        "count": len(sources),
        "sources": sources,
    }


@app.get("/api/stats", tags=["data"])
def get_stats():
    """
    Dashboard stats — overview of the entire system.
    """
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


# ─── STARTUP & SHUTDOWN ────────────────────────────────────────
@app.on_event("startup")
async def startup():
    """Initialize database and start the scheduler."""
    print("\n" + "=" * 50)
    print("  🔍 VerifyPulse API v0.2.0")
    print("  📖 Docs: http://localhost:8000/docs")
    print("  🏥 Health: http://localhost:8000/api/health")
    print("=" * 50 + "\n")

    # Initialize SQLite database
    print("🗄️  Setting up database...")
    init_database()

    # Start automatic fetching
    print("⏰ Starting scheduler...")
    start_scheduler()


@app.on_event("shutdown")
async def shutdown():
    """Clean up on server stop."""
    stop_scheduler()
    print("👋 VerifyPulse shut down cleanly")
