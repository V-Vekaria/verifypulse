"""
VerifyPulse Translation Service
Uses Claude API to batch-translate story titles and summaries into any language.
One Claude call handles the entire visible feed — efficient and fast.
"""

import os
import json
import httpx

ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_MODEL = "claude-haiku-4-5-20251001"  # fast + cheap for translation

SUPPORTED_LANGUAGES = {
    "hi": "Hindi",
    "gu": "Gujarati",
    "ko": "Korean",
    "ar": "Arabic",
    "fr": "French",
    "es": "Spanish",
    "de": "German",
    "ja": "Japanese",
    "zh": "Chinese (Simplified)",
    "pt": "Portuguese",
    "ru": "Russian",
    "ta": "Tamil",
    "te": "Telugu",
    "bn": "Bengali",
    "mr": "Marathi",
}

TRANSLATION_SYSTEM_PROMPT = """You are a professional news translator. Translate the given JSON array of news headlines accurately into the requested language.

Rules:
- Return ONLY a valid JSON array of translated strings, same length and order as input
- Preserve proper nouns (names of people, places, organisations) in their well-known local form if one exists, otherwise keep them as-is
- Keep numbers and dates as-is
- Do NOT add commentary, explanations, or extra text — only the JSON array
- Maintain the factual, neutral tone of news headlines

Example input: ["Two killed in Gaza strike", "Markets fall 3% on tariff fears"]
Example output (Hindi): ["गाजा हमले में दो की मौत", "टैरिफ डर से बाजार 3% गिरे"]"""


def translate_texts(texts: list[str], target_lang_code: str) -> list[str]:
    """
    Translate a list of text strings to the target language in a single Claude call.

    Args:
        texts: List of English text strings (headlines, summaries, etc.)
        target_lang_code: ISO language code e.g. "hi", "ko", "gu"

    Returns:
        List of translated strings, same length and order.
        Falls back to original texts on any failure.
    """
    if not texts:
        return texts

    lang_name = SUPPORTED_LANGUAGES.get(target_lang_code)
    if not lang_name:
        return texts

    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        return texts

    try:
        payload = {
            "model": ANTHROPIC_MODEL,
            "max_tokens": 4096,
            "system": TRANSLATION_SYSTEM_PROMPT,
            "messages": [
                {
                    "role": "user",
                    "content": f"Translate these news headlines into {lang_name}:\n\n{json.dumps(texts, ensure_ascii=False)}",
                }
            ],
        }

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

        raw = response.json()["content"][0]["text"].strip()

        # Strip markdown fences if present
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.strip()

        translated = json.loads(raw)

        if isinstance(translated, list) and len(translated) == len(texts):
            return [str(t) for t in translated]

        # Length mismatch — fall back
        return texts

    except Exception as e:
        print(f"  [WARN] Translation failed ({target_lang_code}): {e}")
        return texts
