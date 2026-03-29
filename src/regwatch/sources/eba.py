"""EBA RSS source (stub)."""

from __future__ import annotations

from datetime import date

from regwatch.models import RawChange
from regwatch.regulations.base import Regulation


class EbaSource:
    id: str = "eba"
    name: str = "EBA"

    def fetch(self, since: date, regulations: list[Regulation]) -> list[RawChange]:
        """Fetch regulatory changes from EBA RSS feed."""
        return []
