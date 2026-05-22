"""
Tests for VerifyPulse Story Timeline / Snapshot system
Run with: python -m pytest tests/test_timeline.py -v
"""

import sys
import os
import sqlite3
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


# ─── HELPERS ────────────────────────────────────────────────────
def _make_temp_db(monkeypatch_or_patch=None):
    """Return path to a fresh temp SQLite db."""
    tmp = tempfile.mktemp(suffix=".db")
    return tmp


SAMPLE_CLUSTERS = [
    {
        "cluster_id": "cluster_aaa",
        "title": "Modi visits Japan",
        "confidence_score": 72.5,
        "articles": [{"id": "1"}, {"id": "2"}],
        "source_count": 2,
    },
    {
        "cluster_id": "cluster_bbb",
        "title": "London flooding",
        "confidence_score": 45.0,
        "articles": [{"id": "3"}],
        "source_count": 1,
    },
]


# ─── TESTS ──────────────────────────────────────────────────────
class TestStorySnapshots:

    def test_save_snapshot_inserts_row(self):
        """save_snapshot should insert one row into story_snapshots."""
        import tempfile
        from unittest.mock import patch

        tmp_db = tempfile.mktemp(suffix=".db")

        with patch("app.services.database.DATABASE_PATH", tmp_db):
            from app.services.database import init_database, save_snapshot, get_story_timeline

            init_database()
            save_snapshot(
                cluster_id="cluster_test",
                confidence_score=65.0,
                article_count=3,
                source_count=2,
            )
            timeline = get_story_timeline("cluster_test")

        assert len(timeline) == 1
        assert timeline[0]["cluster_id"] == "cluster_test"
        assert timeline[0]["confidence_score"] == 65.0
        assert timeline[0]["article_count"] == 3
        assert timeline[0]["source_count"] == 2

        os.unlink(tmp_db)

    def test_snapshot_count_increases_after_each_save(self):
        """Multiple save_snapshot calls should grow the timeline."""
        import tempfile
        from unittest.mock import patch

        tmp_db = tempfile.mktemp(suffix=".db")

        with patch("app.services.database.DATABASE_PATH", tmp_db):
            from app.services.database import init_database, save_snapshot, get_story_timeline

            init_database()
            save_snapshot("cluster_x", 40.0, 1, 1)
            save_snapshot("cluster_x", 55.0, 2, 2)
            save_snapshot("cluster_x", 70.0, 3, 3)

            timeline = get_story_timeline("cluster_x")

        assert len(timeline) == 3
        scores = [t["confidence_score"] for t in timeline]
        assert scores == [40.0, 55.0, 70.0]  # ascending order

        os.unlink(tmp_db)

    def test_timeline_is_sorted_oldest_first(self):
        """Timeline must be sorted ascending by snapshot_at."""
        import tempfile
        from unittest.mock import patch

        tmp_db = tempfile.mktemp(suffix=".db")

        with patch("app.services.database.DATABASE_PATH", tmp_db):
            from app.services.database import init_database, save_snapshot, get_story_timeline

            init_database()
            for score in [30.0, 50.0, 75.0]:
                save_snapshot("cluster_y", score, 1, 1)

            timeline = get_story_timeline("cluster_y")

        timestamps = [t["snapshot_at"] for t in timeline]
        assert timestamps == sorted(timestamps), "Timeline not in ascending order"

        os.unlink(tmp_db)

    def test_save_snapshots_for_clusters_saves_all(self):
        """save_snapshots_for_clusters should save one snapshot per cluster."""
        import tempfile
        from unittest.mock import patch

        tmp_db = tempfile.mktemp(suffix=".db")

        with patch("app.services.database.DATABASE_PATH", tmp_db):
            from app.services.database import init_database, save_snapshots_for_clusters, get_story_timeline

            init_database()
            save_snapshots_for_clusters(SAMPLE_CLUSTERS)

            timeline_a = get_story_timeline("cluster_aaa")
            timeline_b = get_story_timeline("cluster_bbb")

        assert len(timeline_a) == 1
        assert timeline_a[0]["confidence_score"] == 72.5

        assert len(timeline_b) == 1
        assert timeline_b[0]["confidence_score"] == 45.0

        os.unlink(tmp_db)

    def test_empty_timeline_returns_empty_list(self):
        """get_story_timeline for unknown cluster returns empty list, not error."""
        import tempfile
        from unittest.mock import patch

        tmp_db = tempfile.mktemp(suffix=".db")

        with patch("app.services.database.DATABASE_PATH", tmp_db):
            from app.services.database import init_database, get_story_timeline

            init_database()
            result = get_story_timeline("cluster_doesnt_exist")

        assert result == []

        os.unlink(tmp_db)


# ─── RUNNER ─────────────────────────────────────────────────────
if __name__ == "__main__":
    print("Running Timeline Tests...\n")
    passed = failed = 0
    instance = TestStorySnapshots()
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