"""Deterministic classifier for regulatory changes."""

import json
import logging
import re
from collections.abc import Callable

import httpx

from regwatch.models import RawChange
from regwatch.regulations.base import Regulation

logger = logging.getLogger(__name__)

CLASSIFICATION_PROMPT = (
    "Classify this EU regulatory document into one of these regulations:\n"
    "dora, mica, ai_act, psd3, amld6, or \"other\" if none match.\n\n"
    "Title: {title}\n"
    "Description: {description}\n\n"
    'Return ONLY a JSON object: {{"regulation": "<id>"}}'
)

VALID_REGULATIONS = {"dora", "mica", "ai_act", "psd3", "amld6"}


def detect_llm_provider(api_key: str | None) -> str | None:
    """Detect LLM provider from API key prefix."""
    if not api_key:
        return None
    if api_key.startswith("sk-ant-"):
        return "claude"
    if api_key.startswith("sk-"):
        return "openai"
    return None


def create_llm_classifier(api_key: str | None) -> Callable | None:
    """Create an LLM classifier callable for the given API key.

    Returns a callable(title, description) -> str | None, or None if no key.
    """
    provider = detect_llm_provider(api_key)
    if provider is None:
        return None

    def classify(title: str, description: str) -> str | None:
        prompt = CLASSIFICATION_PROMPT.format(title=title, description=description)
        try:
            if provider == "claude":
                response = httpx.post(
                    "https://api.anthropic.com/v1/messages",
                    headers={
                        "x-api-key": api_key,
                        "anthropic-version": "2023-06-01",
                        "content-type": "application/json",
                    },
                    json={
                        "model": "claude-haiku-4-5-20251001",
                        "max_tokens": 100,
                        "messages": [{"role": "user", "content": prompt}],
                    },
                    timeout=30.0,
                )
                response.raise_for_status()
                data = response.json()
                text = data["content"][0]["text"]
            else:
                response = httpx.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": "gpt-4o-mini",
                        "messages": [{"role": "user", "content": prompt}],
                        "max_tokens": 100,
                    },
                    timeout=30.0,
                )
                response.raise_for_status()
                data = response.json()
                text = data["choices"][0]["message"]["content"]

            parsed = json.loads(text)
            regulation = parsed.get("regulation")
            if regulation and regulation in VALID_REGULATIONS:
                return regulation
            return None
        except (json.JSONDecodeError, KeyError, TypeError):
            return None
        except httpx.HTTPError as e:
            logger.warning("LLM classification failed: %s", e)
            return None

    return classify


def classify_regulation(
    raw: RawChange,
    regulations: list[Regulation],
    llm_classify: Callable | None = None,
) -> str | None:
    """Classify which regulation a raw change belongs to.

    Layer 1: Direct CELEX ID match.
    Layer 2: Keyword + EuroVoc scoring (EuroVoc weighted 2x).
    Layer 3: Optional LLM fallback if ambiguous.
    """
    # Layer 1: CELEX direct match
    if raw.celex_id:
        for reg in regulations:
            if raw.celex_id in reg.celex_ids:
                return reg.id

    # Layer 2: Keyword + EuroVoc + source tag scoring
    text = f"{raw.title} {raw.description}".lower()
    scores: dict[str, float] = {}

    for reg in regulations:
        score = 0.0

        # Keyword matching — count each keyword hit
        keyword_hits = 0
        for kw in reg.keywords:
            if kw.lower() in text:
                keyword_hits += 1
        if reg.keywords:
            score += keyword_hits / len(reg.keywords)

        # Source-specific tag matching
        source_tags: list[str] = []
        if raw.source == "esma":
            source_tags = reg.esma_tags
        elif raw.source == "eba":
            source_tags = reg.eba_tags
        tag_hits = sum(1 for tag in source_tags if tag.lower() in text)
        if source_tags:
            score += tag_hits / len(source_tags)

        # EuroVoc matching (weighted 2x)
        eurovoc_hits = 0
        for code in reg.eurovoc_codes:
            if code in raw.eurovoc_codes:
                eurovoc_hits += 1
        if reg.eurovoc_codes:
            score += 2.0 * (eurovoc_hits / len(reg.eurovoc_codes))

        if score > 0:
            scores[reg.id] = score

    if scores:
        return max(scores, key=scores.get)

    # Layer 3: Optional LLM fallback
    if llm_classify is not None:
        return llm_classify(raw)

    return None


# Document type patterns
_TYPE_PATTERNS: list[tuple[str, str]] = [
    ("delegated_act", r"delegated\s+(regulation|act|directive)"),
    ("rts_its", r"(regulatory|implementing)\s+technical\s+standards?"),
    ("guideline", r"guideline"),
    ("consultation", r"consult"),
    ("q_and_a", r"q\s*&\s*a"),
    ("opinion", r"opinion"),
]


def classify_type(title: str) -> str:
    """Classify document type from title using regex patterns."""
    lower = title.lower()
    for doc_type, pattern in _TYPE_PATTERNS:
        if re.search(pattern, lower):
            return doc_type
    return "legislative_act"


# Urgency patterns
_HIGH_URGENCY_PATTERNS = [
    r"enters?\s+into\s+force",
    r"deadline",
    r"final\s+draft",
]


def classify_urgency(title: str, doc_type: str) -> str:
    """Classify urgency based on title keywords and document type."""
    lower = title.lower()

    for pattern in _HIGH_URGENCY_PATTERNS:
        if re.search(pattern, lower):
            return "high"

    if doc_type == "consultation":
        return "high"

    if doc_type in ("q_and_a", "opinion"):
        return "low"

    return "medium"
