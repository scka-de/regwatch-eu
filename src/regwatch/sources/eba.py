"""EBA RSS source for regulatory changes."""

from __future__ import annotations

import logging
from datetime import date
from html.parser import HTMLParser

import feedparser
import httpx

from regwatch.models import RawChange
from regwatch.regulations.base import Regulation

logger = logging.getLogger(__name__)

EBA_RSS_URL = "https://www.eba.europa.eu/news-press/news/rss.xml"


class _HTMLStripper(HTMLParser):
    """Simple HTML tag stripper."""

    def __init__(self) -> None:
        super().__init__()
        self._parts: list[str] = []

    def handle_data(self, data: str) -> None:
        self._parts.append(data)

    def get_text(self) -> str:
        return " ".join(self._parts).strip()


def _strip_html(html: str) -> str:
    """Remove HTML tags and return plain text."""
    stripper = _HTMLStripper()
    stripper.feed(html)
    return stripper.get_text()


class EbaSource:
    id: str = "eba"
    name: str = "EBA"

    def fetch(self, since: date, regulations: list[Regulation]) -> list[RawChange]:
        """Fetch regulatory changes from EBA RSS feed."""
        try:
            response = httpx.get(EBA_RSS_URL, timeout=30.0)
            response.raise_for_status()
        except httpx.TimeoutException:
            logger.warning("EBA RSS request timed out")
            raise
        except httpx.HTTPStatusError as e:
            logger.warning("EBA RSS HTTP error: %s", e.response.status_code)
            raise

        feed = feedparser.parse(response.text)
        results: list[RawChange] = []

        # Collect all keywords from requested regulations
        all_keywords = []
        for reg in regulations:
            all_keywords.extend(kw.lower() for kw in reg.keywords)
            all_keywords.extend(tag.lower() for tag in reg.eba_tags)

        for entry in feed.entries:
            raw = self._parse_entry(entry)
            if raw.date < since:
                continue
            # Filter by regulation keywords in title
            title_lower = raw.title.lower()
            if any(kw in title_lower for kw in all_keywords):
                results.append(raw)

        return results

    def _parse_entry(self, entry: dict) -> RawChange:
        """Parse a feedparser entry into a RawChange."""
        title = entry.get("title", "")
        link = entry.get("link", "")
        summary_html = entry.get("summary", "")

        # Use published_parsed (feedparser standard) for date
        published = entry.get("published_parsed")
        if published:
            parsed_date = date(published.tm_year, published.tm_mon, published.tm_mday)
        else:
            logger.warning("No published date for EBA entry '%s', using today()", title)
            parsed_date = date.today()

        description = _strip_html(summary_html)

        return RawChange(
            title=title,
            date=parsed_date,
            url=link,
            source="eba",
            description=description,
        )
