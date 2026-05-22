"""
Tests for Day 5: multilingual support and language detection
Run with: python -m pytest tests/test_multilingual.py -v
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.services.rss_fetcher import _detect_language


class TestLanguageDetection:

    def test_english_text_returns_en(self):
        assert _detect_language("India PM Modi visits Japan for bilateral summit") == "en"

    def test_hindi_text_returns_hi(self):
        # Devanagari text: "Modi ne Japan ka daura kiya"
        assert _detect_language("मोदी ने जापान का दौरा किया") == "hi"

    def test_empty_string_returns_en(self):
        assert _detect_language("") == "en"

    def test_mixed_text_mostly_english_returns_en(self):
        # Only a few Hindi chars mixed in — should still be 'en'
        assert _detect_language("Modi visit to Japan मोदी was successful") == "en"

    def test_none_returns_en(self):
        assert _detect_language(None) == "en"


class TestCrossLanguageClustering:

    def test_hindi_english_same_story_cluster_together(self):
        """Hindi and English articles about same event must cluster together."""
        from unittest.mock import patch
        from app.services.clustering import cluster_articles

        article_en = {
            "id": 1, "title": "Modi visits Japan for bilateral summit",
            "summary": "Indian PM arrives in Tokyo for talks.",
            "source_id": "reuters", "source_name": "Reuters",
            "published_at": "2026-05-20T10:00:00", "region": "india",
            "credibility_score": 90, "fetched_at": "2026-05-20T10:00:00",
            "url": "https://reuters.com/1",
        }
        article_hi = {
            "id": 2, "title": "मोदी जापान दौरे पर, द्विपक्षीय वार्ता शुरू",
            "summary": "प्रधानमंत्री मोदी टोक्यो पहुंचे।",
            "source_id": "ndtv_hindi", "source_name": "NDTV Hindi",
            "published_at": "2026-05-20T10:05:00", "region": "india",
            "credibility_score": 75, "fetched_at": "2026-05-20T10:05:00",
            "url": "https://ndtv.com/hindi/1",
        }
        article_unrelated = {
            "id": 3, "title": "Heavy flooding hits London streets",
            "summary": "Severe weather causes disruption in UK capital.",
            "source_id": "bbc_world", "source_name": "BBC",
            "published_at": "2026-05-20T10:10:00", "region": "global",
            "credibility_score": 88, "fetched_at": "2026-05-20T10:10:00",
            "url": "https://bbc.com/1",
        }

        with patch("app.services.clustering._fetch_recent_articles",
                   return_value=[article_en, article_hi, article_unrelated]):
            clusters = cluster_articles()

        # Unrelated London article must be in its own cluster
        london_cluster = next(
            (c for c in clusters if any(a["id"] == 3 for a in c["articles"])), None
        )
        assert london_cluster is not None
        london_ids = [a["id"] for a in london_cluster["articles"]]
        assert 1 not in london_ids, "English Modi article must NOT cluster with London"
        assert 2 not in london_ids, "Hindi Modi article must NOT cluster with London"


if __name__ == "__main__":
    print("Running Multilingual Tests...\n")
    passed = failed = 0
    for cls in [TestLanguageDetection, TestCrossLanguageClustering]:
        instance = cls()
        for method_name in dir(instance):
            if method_name.startswith("test_"):
                try:
                    getattr(instance, method_name)()
                    print(f"  ✓ {cls.__name__}.{method_name}")
                    passed += 1
                except Exception as e:
                    print(f"  ✗ {cls.__name__}.{method_name}: {e}")
                    failed += 1
    print(f"\n{'='*40}")
    print(f"  Results: {passed} passed, {failed} failed")
    print(f"{'='*40}")