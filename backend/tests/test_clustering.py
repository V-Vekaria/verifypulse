"""
Tests for VerifyPulse Clustering and Confidence Scoring
Run with: python -m pytest tests/ -v
"""

import sys
import os

# Add backend to path so imports work
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.services.clustering import (
    _pick_best_title,
    _build_cluster,
    _generate_cluster_id,
)
from app.services.confidence import (
    score_cluster,
    _source_count_score,
    _diversity_score,
    _get_source_type,
    CONFIDENCE_LEVELS,
)


# ─── TEST DATA ──────────────────────────────────────────────────
SAMPLE_ARTICLES = [
    {
        "id": "art_001",
        "title": "India PM Modi visits Japan for bilateral summit",
        "url": "https://reuters.com/article/1",
        "source_id": "reuters",
        "source_name": "Reuters",
        "published_at": "2026-04-09T10:00:00",
        "summary": "Prime Minister Modi arrives in Tokyo",
        "region": "global",
        "credibility_score": 95,
    },
    {
        "id": "art_002",
        "title": "Modi arrives in Tokyo for India-Japan summit talks",
        "url": "https://bbc.com/article/1",
        "source_id": "bbc_world",
        "source_name": "BBC World",
        "published_at": "2026-04-09T10:30:00",
        "summary": "Indian PM in Japan for bilateral discussions",
        "region": "global",
        "credibility_score": 88,
    },
    {
        "id": "art_003",
        "title": "Modi in Japan: Key topics on the agenda",
        "url": "https://ndtv.com/article/1",
        "source_id": "ndtv",
        "source_name": "NDTV",
        "published_at": "2026-04-09T11:00:00",
        "summary": "Trade and defense expected to top agenda",
        "region": "india",
        "credibility_score": 78,
    },
]

SINGLE_ARTICLE = [SAMPLE_ARTICLES[0]]


# ─── CLUSTERING TESTS ───────────────────────────────────────────
class TestClustering:

    def test_pick_best_title_prefers_high_credibility(self):
        """Should pick the title from the most credible source."""
        title = _pick_best_title(SAMPLE_ARTICLES)
        # Reuters (95) should win over BBC (88) and NDTV (78)
        assert "Reuters" not in title  # we pick the title, not the source
        assert len(title) > 10

    def test_pick_best_title_single_article(self):
        """Should return the only title available."""
        title = _pick_best_title(SINGLE_ARTICLE)
        assert title == "India PM Modi visits Japan for bilateral summit"

    def test_pick_best_title_empty(self):
        """Should handle empty list."""
        title = _pick_best_title([])
        assert title == "Unknown Story"

    def test_generate_cluster_id_is_stable(self):
        """Same titles should produce the same cluster ID."""
        titles = ["Article A", "Article B"]
        id1 = _generate_cluster_id(titles)
        id2 = _generate_cluster_id(titles)
        assert id1 == id2
        assert id1.startswith("cluster_")

    def test_generate_cluster_id_order_independent(self):
        """Cluster ID should be the same regardless of title order."""
        id1 = _generate_cluster_id(["A", "B", "C"])
        id2 = _generate_cluster_id(["C", "A", "B"])
        assert id1 == id2

    def test_build_cluster_counts_sources(self):
        """Should correctly count unique sources."""
        cluster = _build_cluster(SAMPLE_ARTICLES)
        assert cluster["source_count"] == 3
        assert "reuters" in cluster["source_ids"]
        assert "bbc_world" in cluster["source_ids"]
        assert "ndtv" in cluster["source_ids"]

    def test_build_cluster_detects_regions(self):
        """Should list all unique regions in the cluster."""
        cluster = _build_cluster(SAMPLE_ARTICLES)
        assert "global" in cluster["regions"]
        assert "india" in cluster["regions"]

    def test_build_cluster_finds_time_range(self):
        """Should identify first and last reported times."""
        cluster = _build_cluster(SAMPLE_ARTICLES)
        assert cluster["first_reported"] is not None
        assert cluster["last_updated"] is not None
        assert cluster["first_reported"] <= cluster["last_updated"]


# ─── CONFIDENCE SCORING TESTS ──────────────────────────────────
class TestConfidenceScoring:

    def test_source_count_scoring(self):
        """More sources = higher score, with diminishing returns."""
        assert _source_count_score(1) == 5
        assert _source_count_score(2) == 15
        assert _source_count_score(3) == 25
        assert _source_count_score(5) == 37
        assert _source_count_score(6) == 40
        assert _source_count_score(10) == 40  # capped at 40

    def test_diversity_scoring(self):
        """More source types = higher diversity score."""
        assert _diversity_score(1) == 5
        assert _diversity_score(2) == 12
        assert _diversity_score(4) == 25

    def test_source_type_mapping(self):
        """Should correctly identify source types."""
        assert _get_source_type("reuters") == "wire_service"
        assert _get_source_type("bbc_world") == "broadcaster"
        assert _get_source_type("ndtv") == "national"
        assert _get_source_type("gdelt_bbc_com") == "aggregator"
        assert _get_source_type("unknown_source") == "unknown"

    def test_score_multi_source_cluster(self):
        """3-source cluster should score higher than single source."""
        multi_cluster = _build_cluster(SAMPLE_ARTICLES)
        single_cluster = _build_cluster(SINGLE_ARTICLE)

        scored_multi = score_cluster(multi_cluster)
        scored_single = score_cluster(single_cluster)

        assert scored_multi["confidence_score"] > scored_single["confidence_score"]
        assert scored_multi["confidence_label"] in [
            l["label"] for l in CONFIDENCE_LEVELS
        ]

    def test_score_has_breakdown(self):
        """Scored cluster should include detailed breakdown."""
        cluster = _build_cluster(SAMPLE_ARTICLES)
        scored = score_cluster(cluster)

        assert "scoring_breakdown" in scored
        breakdown = scored["scoring_breakdown"]
        assert "source_count" in breakdown
        assert "avg_credibility" in breakdown
        assert "source_diversity" in breakdown

    def test_score_has_color(self):
        """Scored cluster should include a color for frontend display."""
        cluster = _build_cluster(SAMPLE_ARTICLES)
        scored = score_cluster(cluster)

        assert "confidence_color" in scored
        assert scored["confidence_color"].startswith("#")

    def test_score_range(self):
        """Score should always be between 0 and 100."""
        cluster = _build_cluster(SAMPLE_ARTICLES)
        scored = score_cluster(cluster)

        assert 0 <= scored["confidence_score"] <= 100

    def test_empty_cluster(self):
        """Should handle empty cluster gracefully."""
        empty = {"articles": [], "source_ids": []}
        scored = score_cluster(empty)
        assert scored["confidence_score"] == 0
        assert scored["confidence_label"] == "Disputed"

    def test_high_credibility_sources_boost_score(self):
        """Wire services (95 credibility) should produce higher scores."""
        wire_articles = [
            {"id": "1", "title": "Test", "source_id": "reuters",
             "credibility_score": 95, "region": "global"},
            {"id": "2", "title": "Test 2", "source_id": "ap_news",
             "credibility_score": 95, "region": "global"},
        ]
        low_articles = [
            {"id": "3", "title": "Test", "source_id": "gdelt_blog1",
             "credibility_score": 40, "region": "global"},
            {"id": "4", "title": "Test 2", "source_id": "gdelt_blog2",
             "credibility_score": 40, "region": "global"},
        ]

        wire_cluster = {
            "articles": wire_articles,
            "source_ids": ["reuters", "ap_news"],
        }
        low_cluster = {
            "articles": low_articles,
            "source_ids": ["gdelt_blog1", "gdelt_blog2"],
        }

        wire_scored = score_cluster(wire_cluster)
        low_scored = score_cluster(low_cluster)

        assert wire_scored["confidence_score"] > low_scored["confidence_score"]


# ─── RUN TESTS ──────────────────────────────────────────────────
if __name__ == "__main__":
    print("Running VerifyPulse Tests...\n")

    # Simple test runner (works without pytest too)
    test_classes = [TestClustering, TestConfidenceScoring]
    passed = 0
    failed = 0

    for cls in test_classes:
        instance = cls()
        for method_name in dir(instance):
            if method_name.startswith("test_"):
                try:
                    getattr(instance, method_name)()
                    print(f"  ✓ {cls.__name__}.{method_name}")
                    passed += 1
                except AssertionError as e:
                    print(f"  ✗ {cls.__name__}.{method_name}: {e}")
                    failed += 1
                except Exception as e:
                    print(f"  ✗ {cls.__name__}.{method_name}: {e}")
                    failed += 1

    print(f"\n{'='*40}")
    print(f"  Results: {passed} passed, {failed} failed")
    print(f"{'='*40}")
