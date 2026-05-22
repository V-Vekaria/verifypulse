"""
Tests for VerifyPulse Claim Extractor
Run with: python -m pytest tests/test_claims.py -v
"""

import sys
import os
import json
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.services.claim_extractor import extract_claims, extract_claims_for_cluster


# ─── MOCK HELPERS ───────────────────────────────────────────────
def _mock_claude_response(claims: list[str]):
    """Build a mock httpx response that returns given claims as JSON."""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "content": [{"text": json.dumps(claims)}]
    }
    mock_resp.raise_for_status = MagicMock()
    return mock_resp


SAMPLE_CLUSTER = {
    "cluster_id": "cluster_abc123",
    "title": "Modi visits Japan for bilateral summit",
    "articles": [
        {
            "id": "1",
            "title": "India PM Modi visits Japan for bilateral summit",
            "summary": "Prime Minister Modi arrived in Tokyo on Monday for a two-day bilateral summit. The leaders agreed to increase defence cooperation.",
            "source_id": "reuters",
            "credibility_score": 95,
        },
        {
            "id": "2",
            "title": "Modi in Tokyo for talks",
            "summary": "Indian PM begins Japan visit.",
            "source_id": "bbc_world",
            "credibility_score": 88,
        },
    ],
}


# ─── TESTS ──────────────────────────────────────────────────────
class TestClaimExtractor:

    def test_extract_claims_returns_list(self):
        """Should return a list of strings."""
        mock_claims = [
            "Modi arrived in Tokyo on Monday.",
            "The summit lasts two days.",
            "Leaders agreed to increase defence cooperation.",
        ]
        with patch("app.services.claim_extractor.httpx.post",
                   return_value=_mock_claude_response(mock_claims)):
            with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}):
                result = extract_claims("PM Modi arrived in Tokyo.", "Modi visits Japan")

        assert isinstance(result, list)
        assert len(result) == 3
        assert all(isinstance(c, str) for c in result)

    def test_extract_claims_no_api_key_returns_empty(self):
        """Should return empty list gracefully when no API key set."""
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("ANTHROPIC_API_KEY", None)
            result = extract_claims("Some article text.")

        assert result == []

    def test_extract_claims_handles_markdown_fences(self):
        """Should strip ```json fences from Claude response."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "content": [{"text": '```json\n["Claim one.", "Claim two."]\n```'}]
        }
        mock_resp.raise_for_status = MagicMock()

        with patch("app.services.claim_extractor.httpx.post", return_value=mock_resp):
            with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}):
                result = extract_claims("Some text.")

        assert result == ["Claim one.", "Claim two."]

    def test_extract_claims_handles_api_error_gracefully(self):
        """Should return empty list on HTTP error, not crash."""
        import httpx
        mock_resp = MagicMock()
        mock_resp.status_code = 429
        mock_resp.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Rate limited", request=MagicMock(), response=mock_resp
        )

        with patch("app.services.claim_extractor.httpx.post", return_value=mock_resp):
            with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}):
                result = extract_claims("Some text.")

        assert result == []

    def test_extract_claims_for_cluster_picks_best_article(self):
        """Should use the highest-credibility article (Reuters, score 95)."""
        captured = {}

        def mock_extract(text, title=""):
            captured["title"] = title
            return ["A claim."]

        with patch("app.services.claim_extractor.extract_claims", side_effect=mock_extract):
            result = extract_claims_for_cluster(SAMPLE_CLUSTER)

        # Reuters (95) should be picked over BBC (88)
        assert captured["title"] == "India PM Modi visits Japan for bilateral summit"
        assert result == ["A claim."]

    def test_extract_claims_for_empty_cluster_returns_empty(self):
        """Should handle cluster with no articles gracefully."""
        empty_cluster = {"cluster_id": "x", "title": "Test", "articles": []}
        result = extract_claims_for_cluster(empty_cluster)
        assert result == []


# ─── RUNNER ─────────────────────────────────────────────────────
if __name__ == "__main__":
    print("Running Claim Extractor Tests...\n")
    passed = failed = 0
    instance = TestClaimExtractor()
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