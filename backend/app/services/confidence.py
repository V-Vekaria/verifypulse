"""
VerifyPulse Confidence Scoring Engine
Calculates how trustworthy each story cluster is.

The score is based on three factors:
1. Source count — how many independent sources report this story
2. Source credibility — average credibility of reporting sources
3. Source diversity — are sources from different types (wire, broadcaster, national)?

Output is a 0-100 score mapped to a human-readable label.
"""

from typing import Optional


# ─── CONFIDENCE LABELS ──────────────────────────────────────────
# Maps score ranges to labels and colors (for frontend)
CONFIDENCE_LEVELS = [
    {"min": 80, "max": 100, "label": "Verified",       "color": "#22c55e", "description": "Multiple independent credible sources confirm"},
    {"min": 60, "max": 79,  "label": "Likely Accurate", "color": "#84cc16", "description": "Strong sourcing, not fully independently confirmed"},
    {"min": 40, "max": 59,  "label": "Developing",      "color": "#eab308", "description": "Some corroboration, still evolving"},
    {"min": 20, "max": 39,  "label": "Unverified",      "color": "#f97316", "description": "Limited sources, insufficient evidence"},
    {"min": 0,  "max": 19,  "label": "Disputed",        "color": "#ef4444", "description": "Single source or contradictory reports"},
]


def score_cluster(cluster: dict) -> dict:
    """
    Calculate confidence score for a story cluster.

    Args:
        cluster: A cluster dict from the clustering engine

    Returns:
        The same cluster dict with added fields:
        - confidence_score: float 0-100
        - confidence_label: human-readable label
        - confidence_color: hex color for frontend
        - confidence_description: explanation text
        - scoring_breakdown: detailed scoring factors
    """
    articles = cluster.get("articles", [])
    source_ids = cluster.get("source_ids", [])

    if not articles:
        return _apply_score(cluster, 0.0, {})

    # ── FACTOR 1: Source Count (0-40 points) ────────────────────
    # 1 source = 5pts, 2 = 15pts, 3 = 25pts, 4 = 32pts, 5+ = 40pts
    # Diminishing returns — going from 1→2 sources matters more than 4→5
    source_count = len(source_ids)
    source_count_points = _source_count_score(source_count)

    # ── FACTOR 2: Source Credibility (0-35 points) ──────────────
    # Average credibility of all reporting sources, scaled to 35
    credibility_scores = [a.get("credibility_score", 50) for a in articles]
    avg_credibility = sum(credibility_scores) / len(credibility_scores)
    credibility_points = (avg_credibility / 100) * 35

    # ── FACTOR 3: Source Diversity (0-25 points) ────────────────
    # Different types of sources (wire, broadcaster, national, aggregator)
    # More diversity = higher confidence
    source_types = set()
    for article in articles:
        src_id = article.get("source_id", "")
        source_types.add(_get_source_type(src_id))

    diversity_count = len(source_types)
    diversity_points = _diversity_score(diversity_count)

    # ── FINAL SCORE ─────────────────────────────────────────────
    raw_score = source_count_points + credibility_points + diversity_points
    final_score = min(100.0, max(0.0, raw_score))

    breakdown = {
        "source_count": {
            "value": source_count,
            "points": round(source_count_points, 1),
            "max": 40,
        },
        "avg_credibility": {
            "value": round(avg_credibility, 1),
            "points": round(credibility_points, 1),
            "max": 35,
        },
        "source_diversity": {
            "types": list(source_types),
            "count": diversity_count,
            "points": round(diversity_points, 1),
            "max": 25,
        },
    }

    return _apply_score(cluster, final_score, breakdown)


def _source_count_score(count: int) -> float:
    """
    Score based on number of independent sources.
    Uses logarithmic scaling — each additional source matters less.
    """
    scores = {1: 5, 2: 15, 3: 25, 4: 32, 5: 37}
    if count >= 6:
        return 40.0
    return float(scores.get(count, 0))


def _diversity_score(type_count: int) -> float:
    """Score based on how many different types of sources report the story."""
    scores = {1: 5, 2: 12, 3: 20, 4: 25}
    if type_count >= 4:
        return 25.0
    return float(scores.get(type_count, 0))


def _get_source_type(source_id: str) -> str:
    """
    Map source_id to source type.
    Matches the types defined in config.py.
    """
    type_map = {
        "reuters": "wire_service",
        "ap_news": "wire_service",
        "bbc_world": "broadcaster",
        "aljazeera": "broadcaster",
        "ndtv": "national",
    }
    # GDELT sources start with "gdelt_"
    if source_id.startswith("gdelt_"):
        return "aggregator"

    return type_map.get(source_id, "unknown")


def _apply_score(cluster: dict, score: float, breakdown: dict) -> dict:
    """Apply the confidence score and label to the cluster."""
    score = round(score, 1)

    # Find matching confidence level
    level = CONFIDENCE_LEVELS[-1]  # default to lowest
    for lvl in CONFIDENCE_LEVELS:
        if lvl["min"] <= score <= lvl["max"]:
            level = lvl
            break

    cluster["confidence_score"] = score
    cluster["confidence_label"] = level["label"]
    cluster["confidence_color"] = level["color"]
    cluster["confidence_description"] = level["description"]
    cluster["scoring_breakdown"] = breakdown

    return cluster


def score_all_clusters(clusters: list[dict]) -> list[dict]:
    """
    Score all clusters and sort by confidence (highest first).

    Args:
        clusters: List of cluster dicts from clustering engine

    Returns:
        Same clusters with confidence scores added, sorted by score
    """
    scored = [score_cluster(c) for c in clusters]
    scored.sort(key=lambda c: c["confidence_score"], reverse=True)

    # Print summary
    labels = {}
    for c in scored:
        label = c["confidence_label"]
        labels[label] = labels.get(label, 0) + 1

    print(f"\n📊 Confidence Score Summary:")
    for label, count in labels.items():
        print(f"  • {label}: {count} stories")

    return scored
