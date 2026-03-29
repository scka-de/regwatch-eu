"""Shared utilities for source parsers."""

import re


def strip_html(text: str) -> str:
    """Remove HTML tags and normalize whitespace."""
    clean = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", clean).strip()
