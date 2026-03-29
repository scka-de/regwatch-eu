"""Data models for regwatch-eu."""

import hashlib
from dataclasses import dataclass, field
from datetime import date


def make_change_id(url: str) -> str:
    """Generate a deterministic ID from a URL."""
    return hashlib.sha256(url.encode()).hexdigest()


@dataclass
class RawChange:
    """Raw regulatory change from a source, before classification."""

    title: str
    date: date
    url: str
    source: str
    description: str = ""
    celex_id: str = ""
    eurovoc_codes: list[str] = field(default_factory=list)


@dataclass
class ClassifiedChange:
    """Regulatory change after classification."""

    id: str
    title: str
    date: date
    url: str
    source: str
    regulation: str | None
    type: str
    urgency: str
    summary: str | None
