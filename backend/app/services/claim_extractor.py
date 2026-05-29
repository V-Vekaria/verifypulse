"""
VerifyPulse Claim Extractor
Uses Claude API to extract specific factual claims from news articles.
Turns VerifyPulse from "groups articles" → "verifies specific claims".
"""

import os
import json
import httpx
from typing import Optional

ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_MODEL = "claude-sonnet-4-20250514"

# System prompt — instructs Claude to extract verifiable claims only
EXTRACTION_SYSTEM_PROMPT = """You are a fact-checking assistant. Extract specific, verifiable factual claims from news article text.

Rules:
- Return ONLY a JSON array of claim strings, nothing else
- Each claim must be a single, specific, verifiable statement
- Do NOT include opinions, predictions, or vague statements
- Do NOT include meta-commentary about the article
- Maximum 5 claims per article
- Keep each claim under 20 words

Example output:
["The meeting took place on 15 May 2026.", "Three people were injured in the incident.", "The bill passed with 234 votes in favour."]"""


def extract_claims(article_text: str, article_title: str = "") -> list[str]:
    """
    Extract factual claims from article text using Claude API.

    Args:
        article_text: Full article body or summary
        article_title: Article headline (helps Claude understand context)

    Returns:
        List of factual claim strings, empty list on failure
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        print("  [WARN] ANTHROPIC_API_KEY not set — skipping claim extraction")
        return []

    text = f"Headline: {article_title}\n\n{article_text}" if article_title else article_text

    payload = {
        "model": ANTHROPIC_MODEL,
        "max_tokens": 1000,
        "system": EXTRACTION_SYSTEM_PROMPT,
        "messages": [
            {
                "role": "user",
                "content": f"Extract factual claims from this article:\n\n{text}"
            }
        ],
    }

    try:
        response = httpx.post(
            ANTHROPIC_API_URL,
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json=payload,
            timeout=30.0,
        )
        response.raise_for_status()
        data = response.json()

        raw_text = data["content"][0]["text"].strip()

        # Strip markdown fences if present
        if raw_text.startswith("```"):
            raw_text = raw_text.split("```")[1]
            if raw_text.startswith("json"):
                raw_text = raw_text[4:]
            raw_text = raw_text.strip()

        claims = json.loads(raw_text)
        if isinstance(claims, list):
            return [str(c) for c in claims if c]
        return []

    except httpx.HTTPStatusError as e:
        print(f"  [ERR] Claude API HTTP error: {e.response.status_code}")
        return []
    except json.JSONDecodeError as e:
        print(f"  [ERR] Failed to parse claims JSON: {e}")
        return []
    except Exception as e:
        print(f"  [ERR] Claim extraction failed: {e}")
        return []


def extract_claims_for_cluster(cluster: dict) -> list[str]:
    """
    Extract claims from the highest-credibility article in a cluster.
    Uses only one article to avoid redundancy and save API tokens.

    Args:
        cluster: A scored cluster dict

    Returns:
        List of factual claims
    """
    articles = cluster.get("articles", [])
    if not articles:
        return []

    # Pick most credible article
    best = max(articles, key=lambda a: a.get("credibility_score", 0))
    title = best.get("title", "")
    summary = best.get("summary", "")

    if not summary and not title:
        return []

    text = summary or title
    print(f"  [>>] Extracting claims from: {title[:60]}...")
    claims = extract_claims(text, title)
    print(f"  [OK] Found {len(claims)} claims")
    return claims