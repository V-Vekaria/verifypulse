"""
VerifyPulse Story Clustering Engine
Groups related articles using sentence-transformers semantic embeddings.
Replaces TF-IDF with all-MiniLM-L6-v2 for paraphrase-aware clustering.
"""

import hashlib
from sentence_transformers import SentenceTransformer
import numpy as np

from app.services.database import get_db
from app.config import CLUSTER_SIMILARITY_THRESHOLD, CLUSTER_WINDOW_HOURS

# ─── SETTINGS ────────────────────────────────────────────────────
SIMILARITY_THRESHOLD = CLUSTER_SIMILARITY_THRESHOLD

# Model loaded once at module level — ~90MB download on first run
_MODEL: SentenceTransformer | None = None


def get_model() -> SentenceTransformer:
    """Return the singleton embedding model, loading it if needed."""
    global _MODEL
    if _MODEL is None:
        print("  📦 Loading sentence-transformers model (first run only)...")
        _MODEL = SentenceTransformer("all-MiniLM-L6-v2")
        print("  ✓ Model loaded")
    return _MODEL


def _generate_cluster_id(titles: list[str]) -> str:
    combined = "|".join(sorted(titles))
    return "cluster_" + hashlib.md5(combined.encode()).hexdigest()[:10]


def _pick_best_title(articles: list[dict]) -> str:
    if not articles:
        return "Unknown Story"
    scored = []
    for article in articles:
        title = article.get("title", "")
        cred = article.get("credibility_score", 50)
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
    Fetches recent articles, embeds them with MiniLM, groups by cosine similarity.
    """
    articles = _fetch_recent_articles(hours)
    if len(articles) < 2:
        return [_single_article_cluster(a) for a in articles]

    print(f"\n🧩 Clustering {len(articles)} articles (semantic embeddings)...")

    # Build text inputs: title + summary
    texts = []
    for article in articles:
        text = article.get("title", "")
        summary = article.get("summary", "")
        if summary:
            text += " " + summary
        texts.append(text)

    # Encode all texts to dense vectors
    model = get_model()
    embeddings = model.encode(texts, convert_to_numpy=True, show_progress_bar=False)

    # Normalise for cosine similarity via dot product
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    norms = np.where(norms == 0, 1, norms)  # avoid div-by-zero
    embeddings = embeddings / norms

    # Compute full pairwise similarity matrix
    similarity_matrix = embeddings @ embeddings.T

    # Greedy clustering
    n = len(articles)
    assigned = [False] * n
    clusters = []

    for i in range(n):
        if assigned[i]:
            continue
        cluster_indices = [i]
        assigned[i] = True
        for j in range(i + 1, n):
            if not assigned[j] and similarity_matrix[i, j] >= SIMILARITY_THRESHOLD:
                cluster_indices.append(j)
                assigned[j] = True
        cluster_articles_list = [articles[idx] for idx in cluster_indices]
        clusters.append(_build_cluster(cluster_articles_list))

    clusters.sort(key=lambda c: c["source_count"], reverse=True)

    print(f"  ✓ Created {len(clusters)} story clusters")
    if clusters:
        print(f"  📊 Largest cluster: {clusters[0]['source_count']} sources")

    return clusters


def _fetch_recent_articles(hours: int) -> list[dict]:
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
    source_ids = list(set(a.get("source_id", "") for a in articles))
    regions = list(set(a.get("region", "global") for a in articles))
    dates = sorted([a.get("published_at") for a in articles if a.get("published_at")])
    return {
        "cluster_id": _generate_cluster_id([a.get("title", "") for a in articles]),
        "title": _pick_best_title(articles),
        "articles": articles,
        "source_count": len(source_ids),
        "source_ids": source_ids,
        "regions": regions,
        "first_reported": dates[0] if dates else None,
        "last_updated": dates[-1] if dates else None,
    }


def save_cluster_assignments(clusters: list[dict]):
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