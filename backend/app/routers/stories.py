"""
VerifyPulse API Router — Stories
All story-related endpoints with proper documentation.
"""

from fastapi import APIRouter, Query, HTTPException

from app.services.clustering import cluster_articles, save_cluster_assignments
from app.services.confidence import score_all_clusters, CONFIDENCE_LEVELS
from app.services.claim_extractor import extract_claims_for_cluster
from app.services.database import get_story_timeline, save_snapshots_for_clusters

router = APIRouter(prefix="/api", tags=["stories"])


@router.get("/stories")
def list_stories(
    region: str | None = Query(
        None, description="Filter by region: global, india, east_asia, americas"
    ),
    hours: int = Query(48, description="Time window in hours (default 48)"),
    min_confidence: float = Query(
        0, description="Minimum confidence score 0-100 (default 0)"
    ),
):
    """
    **The main endpoint** — returns clustered news stories with confidence scores.

    Each story groups related articles from multiple sources and calculates
    a trust score based on source count, credibility, and diversity.

    Confidence labels:
    - **Verified** (80-100): Multiple independent credible sources confirm
    - **Likely Accurate** (60-79): Strong sourcing, not fully confirmed
    - **Developing** (40-59): Some corroboration, still evolving
    - **Unverified** (20-39): Limited sources
    - **Disputed** (0-19): Single source or contradictions
    """
    clusters = cluster_articles(hours=hours)
    scored = score_all_clusters(clusters)

    if region:
        scored = [c for c in scored if region in c.get("regions", [])]

    if min_confidence > 0:
        scored = [
            c for c in scored if c.get("confidence_score", 0) >= min_confidence
        ]

    if scored:
        save_cluster_assignments(scored)
        save_snapshots_for_clusters(scored)  # record timeline snapshot

    return {
        "count": len(scored),
        "hours": hours,
        "region": region or "all",
        "stories": [_format_story(c) for c in scored],
    }


@router.get("/stories/{cluster_id}")
def get_story_detail(cluster_id: str, hours: int = 48):
    """
    Full detail for a single story — all articles, sources, and scoring breakdown.
    Powers the **"Why we trust this"** transparency section on the frontend.
    """
    clusters = cluster_articles(hours=hours)
    scored = score_all_clusters(clusters)

    for cluster in scored:
        if cluster["cluster_id"] == cluster_id:
            return {"found": True, "story": cluster}

    return {
        "found": False,
        "story": None,
        "message": f"No story found with cluster_id: {cluster_id}",
    }


@router.get("/stories/{cluster_id}/claims")
def get_story_claims(cluster_id: str, hours: int = 48):
    """
    **Claude-powered claim extraction** — returns specific verifiable factual claims
    from the most credible article in a story cluster.

    Requires ANTHROPIC_API_KEY environment variable to be set.
    Returns empty claims list gracefully if key is missing.
    """
    clusters = cluster_articles(hours=hours)
    scored = score_all_clusters(clusters)

    target = None
    for cluster in scored:
        if cluster["cluster_id"] == cluster_id:
            target = cluster
            break

    if not target:
        raise HTTPException(
            status_code=404,
            detail=f"No story found with cluster_id: {cluster_id}"
        )

    claims = extract_claims_for_cluster(target)

    return {
        "cluster_id": cluster_id,
        "title": target["title"],
        "claims": claims,
        "claim_count": len(claims),
        "source_article": target["articles"][0]["title"] if target["articles"] else None,
    }


@router.get("/stories/{cluster_id}/timeline")
def get_story_timeline_endpoint(cluster_id: str):
    """
    **Story timeline** — returns confidence score history for a cluster over time.

    Shows how a story's trustworthiness evolved as more sources picked it up.
    Each point represents one fetch cycle.

    Use this to power a confidence-over-time chart on the frontend.
    """
    snapshots = get_story_timeline(cluster_id)

    if not snapshots:
        raise HTTPException(
            status_code=404,
            detail=f"No timeline found for cluster_id: {cluster_id}. Story may be too new."
        )

    return {
        "cluster_id": cluster_id,
        "snapshot_count": len(snapshots),
        "first_seen": snapshots[0]["snapshot_at"] if snapshots else None,
        "last_seen": snapshots[-1]["snapshot_at"] if snapshots else None,
        "current_confidence": snapshots[-1]["confidence_score"] if snapshots else None,
        "timeline": snapshots,
    }


@router.get("/confidence-levels")
def get_confidence_levels():
    """
    Returns all confidence level definitions.
    Useful for frontend to build legends and filter UI.
    """
    return {"levels": CONFIDENCE_LEVELS}


def _format_story(c: dict) -> dict:
    """Format a cluster for the API response (exclude raw articles for list view)."""
    return {
        "cluster_id": c["cluster_id"],
        "title": c["title"],
        "confidence_score": c["confidence_score"],
        "confidence_label": c["confidence_label"],
        "confidence_color": c["confidence_color"],
        "confidence_description": c["confidence_description"],
        "source_count": c["source_count"],
        "source_ids": c["source_ids"],
        "regions": c["regions"],
        "first_reported": c["first_reported"],
        "last_updated": c["last_updated"],
        "article_count": len(c["articles"]),
        "scoring_breakdown": c["scoring_breakdown"],
    }