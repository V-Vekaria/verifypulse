"""
VerifyPulse Story Clustering Engine
Groups related articles about the same event using TF-IDF text similarity.
This is the core intelligence — it answers "which articles are about the same story?"
"""

import hashlib
from datetime import datetime
from typing import Optional
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

from app.services.database import get_db


# ─── SETTINGS ───────────────────────────────────────────────────
# Two articles with >= 0.3 cosine similarity are about the same story.
# 0.3 is deliberately lenient — catches "India PM visits Japan" and
# "Modi arrives in Tokyo for bilateral summit" as the same story.
# Higher threshold = fewer clusters but more precise.
SIMILARITY_THRESHOLD = 0.30

# Only cluster articles from the last N hours (keeps it fast)
CLUSTER_WINDOW_HOURS = 48


def _generate_cluster_id(titles: list[str]) -> str:
    """Create a stable cluster ID from the combined titles."""
    combined = "|".join(sorted(titles))
    return "cluster_" + hashlib.md5(combined.encode()).hexdigest()[:10]


def _pick_best_title(articles: list[dict]) -> str:
    """
    Choose the best headline for a cluster.
    Prefers titles from high-credibility sources that are medium length
    (not too short, not too long).
    """
    if not articles:
        return "Unknown Story"

    # Score each title: credibility + length penalty
    scored = []
    for article in articles:
        title = article.get("title", "")
        cred = article.get("credibility_score", 50)
        # Ideal title length is 40-100 chars
        length = len(title)
        length_score = 1.0
        if length < 20:
            length_score = 0.5
        elif length > 120:
            length_score = 0.7
        scored.append((cred * length_score, title))

    scored.sort(reverse=True)
    return scored[0][1]


def cluster_articles(hours: int = CLUSTER_WINDOW_HOURS) -> list[dict]:
    """
    Main clustering function.
    Fetches recent articles, groups them by similarity, and returns clusters.

    Args:
        hours: Only consider articles from the last N hours

    Returns:
        List of cluster dicts, each containing:
        - cluster_id: unique identifier
        - title: best representative headline
        - articles: list of article dicts in this cluster
        - source_count: number of unique sources
        - source_ids: list of unique source IDs
        - regions: list of regions covered
        - first_reported: earliest publish date
        - last_updated: latest publish date
    """
    # Step 1: Fetch recent articles
    articles = _fetch_recent_articles(hours)
    if len(articles) < 2:
        # Not enough articles to cluster — return each as its own cluster
        return [_single_article_cluster(a) for a in articles]

    print(f"\n🧩 Clustering {len(articles)} articles...")

    # Step 2: Build TF-IDF matrix from titles + summaries
    texts = []
    for article in articles:
        text = article.get("title", "")
        summary = article.get("summary", "")
        if summary:
            text += " " + summary
        texts.append(text)

    vectorizer = TfidfVectorizer(
        stop_words="english",
        max_features=5000,
        ngram_range=(1, 2),  # unigrams + bigrams for better matching
    )

    try:
        tfidf_matrix = vectorizer.fit_transform(texts)
    except ValueError:
        # All texts are empty or stop words only
        print("  ⚠ Could not vectorize articles — returning unclustered")
        return [_single_article_cluster(a) for a in articles]

    # Step 3: Compute pairwise similarity
    similarity_matrix = cosine_similarity(tfidf_matrix)

    # Step 4: Greedy clustering using similarity threshold
    n = len(articles)
    assigned = [False] * n
    clusters = []

    for i in range(n):
        if assigned[i]:
            continue

        # Start a new cluster with article i
        cluster_indices = [i]
        assigned[i] = True

        # Find all articles similar to article i
        for j in range(i + 1, n):
            if assigned[j]:
                continue
            if similarity_matrix[i, j] >= SIMILARITY_THRESHOLD:
                cluster_indices.append(j)
                assigned[j] = True

        # Build the cluster dict
        cluster_articles_list = [articles[idx] for idx in cluster_indices]
        cluster = _build_cluster(cluster_articles_list)
        clusters.append(cluster)

    # Sort by source count (most corroborated first)
    clusters.sort(key=lambda c: c["source_count"], reverse=True)

    print(f"  ✓ Created {len(clusters)} story clusters")
    print(f"  📊 Largest cluster: {clusters[0]['source_count']} sources" if clusters else "")

    return clusters


def _fetch_recent_articles(hours: int) -> list[dict]:
    """Fetch articles from database within the time window."""
    with get_db() as conn:
        rows = conn.execute("""
            SELECT id, title, url, source_id, source_name,
                   published_at, summary, region, credibility_score, fetched_at
            FROM articles
            WHERE fetched_at >= datetime('now', ?)
            ORDER BY published_at DESC
        """, (f"-{hours} hours",)).fetchall()
        return [dict(row) for row in rows]


def _single_article_cluster(article: dict) -> dict:
    """Wrap a single article as its own cluster."""
    return {
        "cluster_id": _generate_cluster_id([article.get("title", "")]),
        "title": article.get("title", "Unknown"),
        "articles": [article],
        "source_count": 1,
        "source_ids": [article.get("source_id", "")],
        "regions": [article.get("region", "global")],
        "first_reported": article.get("published_at"),
        "last_updated": article.get("published_at"),
    }


def _build_cluster(articles: list[dict]) -> dict:
    """Build a cluster dict from a group of related articles."""
    source_ids = list(set(a.get("source_id", "") for a in articles))
    regions = list(set(a.get("region", "global") for a in articles))

    # Find time range
    dates = []
    for a in articles:
        pub = a.get("published_at")
        if pub:
            dates.append(pub)

    dates.sort()
    first = dates[0] if dates else None
    last = dates[-1] if dates else None

    return {
        "cluster_id": _generate_cluster_id([a.get("title", "") for a in articles]),
        "title": _pick_best_title(articles),
        "articles": articles,
        "source_count": len(source_ids),
        "source_ids": source_ids,
        "regions": regions,
        "first_reported": first,
        "last_updated": last,
    }


def save_cluster_assignments(clusters: list[dict]):
    """
    Write cluster_id back to the articles table so we can
    query articles by cluster later.
    """
    with get_db() as conn:
        for cluster in clusters:
            cluster_id = cluster["cluster_id"]
            for article in cluster["articles"]:
                article_id = article.get("id")
                if article_id:
                    conn.execute(
                        "UPDATE articles SET cluster_id = ? WHERE id = ?",
                        (cluster_id, article_id),
                    )

    print(f"  💾 Saved cluster assignments for {len(clusters)} clusters")
