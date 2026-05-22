"""
Tests for Day 6: Daily report generator
Run with: python -m pytest tests/test_report.py -v
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.services.report_generator import generate_daily_report, _fallback_markdown


SAMPLE_CLUSTERS = [
    {
        "cluster_id": "cluster_aaa",
        "title": "Unverified claim about election results",
        "confidence_score": 15.0,
        "confidence_label": "Disputed",
        "source_count": 1,
        "regions": ["global"],
        "articles": [{"id": "1"}],
    },
    {
        "cluster_id": "cluster_bbb",
        "title": "Modi visits Japan",
        "confidence_score": 85.0,
        "confidence_label": "Verified",
        "source_count": 4,
        "regions": ["india"],
        "articles": [{"id": "2"}, {"id": "3"}],
    },
    {
        "cluster_id": "cluster_ccc",
        "title": "Disputed health claim spreading online",
        "confidence_score": 22.0,
        "confidence_label": "Unverified",
        "source_count": 1,
        "regions": ["global"],
        "articles": [{"id": "4"}],
    },
]


class TestReportGenerator:

    def test_report_filters_low_confidence_only(self):
        """Report should only include stories below threshold (40)."""
        report = generate_daily_report(SAMPLE_CLUSTERS)
        assert report["story_count"] == 2  # 15.0 and 22.0, not 85.0
        titles = [s["title"] for s in report["stories"]]
        assert "Modi visits Japan" not in titles

    def test_report_has_required_fields(self):
        """Report must have date, story_count, summary, stories, markdown."""
        report = generate_daily_report(SAMPLE_CLUSTERS)
        assert "date" in report
        assert "story_count" in report
        assert "summary" in report
        assert "stories" in report
        assert "markdown" in report

    def test_empty_clusters_returns_clean_report(self):
        """No low-confidence stories should return clean all-clear report."""
        high_conf = [
            {"cluster_id": "x", "title": "Test", "confidence_score": 90.0,
             "confidence_label": "Verified", "source_count": 3,
             "regions": ["global"], "articles": [{"id": "1"}]}
        ]
        report = generate_daily_report(high_conf)
        assert report["story_count"] == 0
        assert "No low-confidence" in report["summary"]

    def test_fallback_markdown_contains_story_titles(self):
        """Fallback markdown must include story titles."""
        stories = [
            {"title": "Test story A", "confidence_score": 20.0,
             "confidence_label": "Unverified", "source_count": 1},
        ]
        md = _fallback_markdown(stories)
        assert "Test story A" in md
        assert "VerifyPulse Daily Report" in md

    def test_report_markdown_is_string(self):
        """Markdown field must always be a non-empty string."""
        report = generate_daily_report(SAMPLE_CLUSTERS)
        assert isinstance(report["markdown"], str)
        assert len(report["markdown"]) > 0


if __name__ == "__main__":
    print("Running Report Generator Tests...\n")
    passed = failed = 0
    instance = TestReportGenerator()
    for method_name in dir(instance):
        if method_name.startswith("test_"):
            try:
                getattr(instance, method_name)()
                print(f"  ✓ {method_name}")
                passed += 1
            except Exception as e:
                print(f"  ✗ {method_name}: {e}")
                failed += 1
    print(f"\n{'='*40}")
    print(f"  Results: {passed} passed, {failed} failed")
    print(f"{'='*40}")