"""Deterministic classifier for regulatory changes."""

import re
from collections.abc import Callable

from regwatch.models import RawChange
from regwatch.regulations.base import Regulation


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
