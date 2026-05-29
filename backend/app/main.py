"""
VerifyPulse — Main Application
Real-time news verification dashboard.

Run with: uvicorn app.main:app --reload
"""

import sys
if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf-8-sig"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.routers import stories, data
from app.services.database import init_database
from app.services.scheduler import start_scheduler, stop_scheduler
from app.models import HealthResponse
from app.services.database import get_article_count, get_unique_source_count, get_last_fetch
from app.services.clustering import get_model

# ─── APP SETUP ──────────────────────────────────────────────────
app = FastAPI(
    title="VerifyPulse API",
    description="""
## Real-time news verification and confidence scoring

VerifyPulse aggregates news from multiple sources, clusters related stories,
and scores each one for trustworthiness.

### How it works:
1. **Aggregate** — Pull from Reuters, AP, BBC, Al Jazeera, NDTV + GDELT
2. **Cluster** — Group related articles using sentence-transformers semantic embeddings
3. **Score** — Calculate confidence from source count, credibility, and diversity
4. **Serve** — Present scored stories via REST API

### Key endpoints:
- `GET /api/stories` — Clustered stories with confidence scores
- `GET /api/stories/{id}` — Full detail with "Why we trust this" breakdown
- `GET /api/stats` — System overview
    """,
    version="0.4.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── REGISTER ROUTERS ──────────────────────────────────────────
app.include_router(stories.router)
app.include_router(data.router)


# ─── ROOT & HEALTH ─────────────────────────────────────────────
@app.get("/", tags=["health"], include_in_schema=False)
def root():
    """Serve the frontend dashboard."""
    frontend_path = Path(__file__).parent.parent.parent / "frontend" / "index.html"
    if frontend_path.exists():
        return FileResponse(str(frontend_path))
    return {
        "app": "VerifyPulse",
        "version": "0.4.0",
        "status": "running",
        "docs": "/docs",
    }


@app.get("/api/health", response_model=HealthResponse, tags=["health"])
def health_check():
    last = get_last_fetch()
    return HealthResponse(
        status="ok",
        total_articles=get_article_count(),
        total_sources=get_unique_source_count(),
        last_fetch=last["fetched_at"] if last else None,
    )


# ─── LIFECYCLE ──────────────────────────────────────────────────
@app.on_event("startup")
async def startup():
    print("\n" + "=" * 50)
    print("  VerifyPulse API v0.4.0")
    print("  Docs: http://localhost:8000/docs")
    print("  Stories: http://localhost:8000/api/stories")
    print("=" * 50 + "\n")

    init_database()
    get_model()        # warm up sentence-transformers model at boot
    start_scheduler()


@app.on_event("shutdown")
async def shutdown():
    stop_scheduler()