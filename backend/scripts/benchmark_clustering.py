"""
Benchmark: semantic clustering speed and quality.
Run from backend/ folder:
    python scripts/benchmark_clustering.py
"""

import time
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

BENCH_ARTICLES = [
    {"id": i, "title": t, "summary": s, "source_id": "reuters",
     "source_name": "Reuters", "published_at": "2026-05-21T10:00:00",
     "region": "global", "credibility_score": 85,
     "fetched_at": "2026-05-21T10:00:00", "url": f"https://example.com/{i}"}
    for i, (t, s) in enumerate([
        ("Modi visits Japan for bilateral summit", "PM arrives in Tokyo"),
        ("Indian PM Modi arrives in Tokyo for talks", "Bilateral summit begins"),
        ("Modi in Japan: trade and defence on agenda", "Key topics discussed"),
        ("Heavy rain floods London streets", "UK capital hit by storms"),
        ("London flood warning issued by Met Office", "Severe weather alert"),
        ("NASA launches Artemis moon mission", "Rocket lifts off from Kennedy"),
        ("Artemis spacecraft heads to lunar orbit", "Moon mission underway"),
        ("US economy adds 200k jobs in April", "Labour market stays strong"),
        ("April jobs report beats expectations", "Unemployment holds at 3.8%"),
        ("Tech stocks rally on earnings reports", "S&P 500 up 1.2% Friday"),
    ])
]


def benchmark_semantic():
    from unittest.mock import patch
    from app.services.clustering import cluster_articles

    print("\n🔬 Benchmarking sentence-transformers clustering...")
    print(f"   Articles: {len(BENCH_ARTICLES)}")

    print("   Warming up model...")
    with patch("app.services.clustering._fetch_recent_articles",
               return_value=BENCH_ARTICLES):
        cluster_articles()

    times = []
    clusters = []
    for run in range(3):
        start = time.perf_counter()
        with patch("app.services.clustering._fetch_recent_articles",
                   return_value=BENCH_ARTICLES):
            clusters = cluster_articles()
        elapsed = time.perf_counter() - start
        times.append(elapsed)
        print(f"   Run {run + 1}: {elapsed:.3f}s → {len(clusters)} clusters")

    avg = sum(times) / len(times)
    print(f"\n   ✓ Average: {avg:.3f}s over 3 runs")
    print(f"   ✓ Clusters formed: {len(clusters)}")
    for c in clusters:
        print(f"     • [{c['source_count']} src] {c['title'][:50]}")


if __name__ == "__main__":
    benchmark_semantic()
    print("\n✅ Benchmark complete.")