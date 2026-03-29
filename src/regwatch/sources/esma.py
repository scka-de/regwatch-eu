"""ESMA RSS source for regulatory changes."""

from __future__ import annotations

import logging
import re
from datetime import date

import feedparser
import httpx

from regwatch.models import RawChange
from regwatch.regulations.base import Regulation
from regwatch.sources._utils import strip_html

logger = logging.getLogger(__name__)

ESMA_RSS_URL = "https://www.esma.europa.eu/rss.xml"

# Matches "15 March 2026" style dates
_DATE_REGEX = re.compile(
    r"(\d{1,2})\s+(January|February|March|April|May|June|July|"
    r"August|September|October|November|December)\s+(\d{4})"
)

_MONTH_MAP = {
    "January": 1, "February": 2, "March": 3, "April": 4,
    "May": 5, "June": 6, "July": 7, "August": 8,
    "September": 9, "October": 10, "November": 11, "December": 12,
}

# Regex to extract datetime from <time datetime="..."> tag
_TIME_TAG_REGEX = re.compile(r'<time\s+datetime="(\d{4}-\d{2}-\d{2})[T"]')


class EsmaSource:
    id: str = "esma"
    name: str = "ESMA"

    def fetch(self, since: date, regulations: list[Regulation]) -> list[RawChange]:
        """Fetch regulatory changes from ESMA RSS feed."""
        try:
            response = httpx.get(ESMA_RSS_URL, timeout=30.0)
            response.raise_for_status()
        except httpx.TimeoutException:
            logger.warning("ESMA RSS request timed out")
            raise
        except httpx.HTTPStatusError as e:
            logger.warning("ESMA RSS HTTP error: %s", e.response.status_code)
            raise

        feed = feedparser.parse(response.text)
        results: list[RawChange] = []

        # Collect all keywords from requested regulations
        all_keywords = []
        for reg in regulations:
            all_keywords.extend(kw.lower() for kw in reg.keywords)
            all_keywords.extend(tag.lower() for tag in reg.esma_tags)

        for entry in feed.entries:
            raw = self._parse_entry(entry)
            if raw is None or not raw.url:
                continue
            if raw.date < since:
                continue
            # Filter by regulation keywords in title
            title_lower = raw.title.lower()
            if any(kw in title_lower for kw in all_keywords):
                results.append(raw)

        return results

    def _parse_entry(self, entry: dict) -> RawChange | None:
        """Parse a feedparser entry into a RawChange."""
        title = entry.get("title", "").strip()
        link = entry.get("link", "")
        if not title or not link:
            return None
        summary_html = entry.get("summary", "")

        parsed_date = self._extract_date(summary_html)
        description = strip_html(summary_html)

        return RawChange(
            title=title,
            date=parsed_date,
            url=link,
            source="esma",
            description=description,
        )

    def _extract_date(self, html: str) -> date:
        """Extract date from HTML using a fallback chain.

        1. <time datetime="..."> tag
        2. Regex for "DD Month YYYY" pattern
        3. date.today() as last resort
        """
        # Try <time datetime="..."> tag
        match = _TIME_TAG_REGEX.search(html)
        if match:
            return date.fromisoformat(match.group(1))

        # Try "DD Month YYYY" regex
        match = _DATE_REGEX.search(html)
        if match:
            day = int(match.group(1))
            month = _MONTH_MAP[match.group(2)]
            year = int(match.group(3))
            return date(year, month, day)

        # Last resort
        logger.warning("Could not extract date from ESMA entry, using today()")
        return date.today()
