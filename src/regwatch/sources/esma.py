"""ESMA RSS source (stub)."""

from __future__ import annotations

from datetime import date

from regwatch.models import RawChange
from regwatch.regulations.base import Regulation


class EsmaSource:
    id: str = "esma"
    name: str = "ESMA"

    def fetch(self, since: date, regulations: list[Regulation]) -> list[RawChange]:
        """Fetch regulatory changes from ESMA RSS feed."""
        return []
