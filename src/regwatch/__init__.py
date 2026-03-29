"""regwatch-eu: Monitor EU regulatory changes."""

from __future__ import annotations

import logging
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

from regwatch.cache import Cache
from regwatch.classifier import (
    classify_regulation,
    classify_type,
    classify_urgency,
    create_llm_classifier,
)
from regwatch.models import ClassifiedChange, make_change_id
from regwatch.registry import get_regulations, get_sources

__version__ = "0.1.0"
logger = logging.getLogger(__name__)
DEFAULT_CACHE_DIR = str(Path.home() / ".regwatch")


class RegWatch:
    """Main entry point for monitoring EU regulatory changes."""

    def __init__(
        self,
        *,
        cache_dir: str = DEFAULT_CACHE_DIR,
        llm_api_key: str | None = None,
    ) -> None:
        cache_path = Path(cache_dir)
        cache_path.mkdir(parents=True, exist_ok=True)
        self._cache = Cache(str(cache_path / "cache.db"))
        self._regulations = get_regulations()
        self._sources = get_sources()
        self._llm_api_key = llm_api_key
        self._llm_classify = create_llm_classifier(llm_api_key)

    def update(self, *, source: str | None = None) -> dict[str, int]:
        """Fetch latest changes from sources and classify them.

        Returns a dict mapping source id to count of new items (-1 on failure).
        """
        stats: dict[str, int] = {}
        sources = (
            self._sources
            if not source
            else [s for s in self._sources if s.id == source]
        )
        for src in sources:
            since = self._cache.last_update(src.id)
            if since is None:
                since = date.today() - timedelta(days=180)
            try:
                raw_changes = src.fetch(since=since, regulations=self._regulations)
            except Exception as e:
                logger.warning("Source %s failed: %s", src.id, e)
                stats[src.id] = -1
                continue
            classified = []
            for raw in raw_changes:
                regulation = classify_regulation(
                    raw, self._regulations, llm_classify=self._llm_classify
                )
                doc_type = classify_type(raw.title)
                urgency = classify_urgency(raw.title, doc_type)
                classified.append(
                    ClassifiedChange(
                        id=make_change_id(raw.url),
                        title=raw.title,
                        date=raw.date,
                        url=raw.url,
                        source=raw.source,
                        regulation=regulation,
                        type=doc_type,
                        urgency=urgency,
                        summary=None,
                    )
                )
            stats[src.id] = self._cache.upsert(classified)
        return stats

    def check(
        self,
        *,
        regulations: list[str] | None = None,
        since: str | None = None,
        types: list[str] | None = None,
        sources: list[str] | None = None,
    ) -> pd.DataFrame:
        """Query regulatory changes from local cache."""
        since_date = (
            date.fromisoformat(since) if since else date.today() - timedelta(days=30)
        )
        results = self._cache.query(
            regulations=regulations,
            since=since_date,
            types=types,
            sources=sources,
        )
        if not results:
            return pd.DataFrame(
                columns=[
                    "date",
                    "title",
                    "regulation",
                    "type",
                    "source",
                    "urgency",
                    "url",
                    "summary",
                ]
            )
        return pd.DataFrame(
            [
                {
                    "date": r.date,
                    "title": r.title,
                    "regulation": r.regulation,
                    "type": r.type,
                    "source": r.source,
                    "urgency": r.urgency,
                    "url": r.url,
                    "summary": r.summary,
                }
                for r in results
            ]
        )

    def regulations(self) -> list[str]:
        """Return list of supported regulation IDs."""
        return [r.id for r in self._regulations]

    def sources(self) -> list[str]:
        """Return list of registered source IDs."""
        return [s.id for s in self._sources]
