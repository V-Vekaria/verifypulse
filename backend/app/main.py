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
from app.models import HealthResponse

# ─── APP SETUP ──────────────────────────────────────────────────
app = FastAPI(
    title="VerifyPulse API",
    description="Real-time news verification and confidence scoring",
    version="0.1.0",
)

# Allow frontend to connect (Day 5)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── IN-MEMORY STORE (replaced with SQLite on Day 2) ───────────
article_store: list[dict] = []
last_fetch_time: str | None = None


# ─── ROUTES ─────────────────────────────────────────────────────
@app.get("/", tags=["health"])
def root():
    """Root endpoint — confirms the API is running."""
    return {
        "app": "VerifyPulse",
        "version": "0.1.0",
        "status": "running",
        "docs": "/docs",
    }


@app.get("/api/health", response_model=HealthResponse, tags=["health"])
def health_check():
    """Health check with basic stats."""
    unique_sources = set(a.get("source_id") for a in article_store)
    return HealthResponse(
        status="ok",
        total_articles=len(article_store),
        total_sources=len(unique_sources),
        last_fetch=last_fetch_time,
    )


@app.post("/api/fetch", tags=["data"])
def trigger_fetch():
    """
    Manually trigger a news fetch from all sources.
    In Day 2 this becomes automatic with APScheduler.
    """
    global article_store, last_fetch_time

    # Fetch from RSS
    rss_articles = fetch_all_rss()

    # Fetch from GDELT
    gdelt_articles = fetch_gdelt_by_regions()

    # Combine and deduplicate by ID
    all_articles = rss_articles + gdelt_articles
    seen_ids = set()
    unique = []
    for article in all_articles:
        if article.id not in seen_ids:
            seen_ids.add(article.id)
            unique.append(article.model_dump())

    article_store = unique
    last_fetch_time = datetime.now().isoformat()

    return {
        "status": "success",
        "rss_count": len(rss_articles),
        "gdelt_count": len(gdelt_articles),
        "total_unique": len(unique),
        "fetched_at": last_fetch_time,
    }


@app.get("/api/articles", tags=["data"])
def get_articles(region: str | None = None, limit: int = 50):
    """
    Get fetched articles, optionally filtered by region.
    This is a simple Day 1 endpoint — replaced with /api/stories on Day 4.
    """
    articles = article_store

    if region:
        articles = [a for a in articles if a.get("region") == region]

    # Sort by published date (newest first)
    articles.sort(
        key=lambda a: a.get("published_at") or "1970-01-01",
        reverse=True,
    )

    return {
        "count": len(articles[:limit]),
        "region": region or "all",
        "articles": articles[:limit],
    }


# ─── STARTUP ────────────────────────────────────────────────────
@app.on_event("startup")
async def startup_message():
    print("\n" + "=" * 50)
    print("  🔍 VerifyPulse API v0.1.0")
    print("  📖 Docs: http://localhost:8000/docs")
    print("  🏥 Health: http://localhost:8000/api/health")
    print("=" * 50 + "\n")
