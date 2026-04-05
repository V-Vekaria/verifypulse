"""
VerifyPulse Data Models
Pydantic models for articles, sources, and API responses.
"""

from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class Article(BaseModel):
    """A single news article from any source."""

    id: Optional[str] = None
    title: str
    url: str
    source_id: str
    source_name: str
    published_at: Optional[datetime] = None
    summary: Optional[str] = None
    region: str = "global"
    credibility_score: int = 50
    fetched_at: datetime = datetime.now()

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class StoryCluster(BaseModel):
    """A group of related articles about the same event."""

    id: Optional[str] = None
    title: str  # representative headline
    articles: list[Article] = []
    source_count: int = 0
    confidence_score: float = 0.0
    confidence_label: str = "unverified"
    regions: list[str] = []
    first_reported: Optional[datetime] = None
    last_updated: Optional[datetime] = None


class HealthResponse(BaseModel):
    """API health check response."""

    status: str = "ok"
    total_articles: int = 0
    total_sources: int = 0
    last_fetch: Optional[str] = None
