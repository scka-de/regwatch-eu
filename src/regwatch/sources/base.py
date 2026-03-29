"""Base source protocol."""

from __future__ import annotations

from datetime import date
from typing import Protocol

from regwatch.models import RawChange
from regwatch.regulations.base import Regulation


class Source(Protocol):
    id: str
    name: str

    def fetch(self, since: date, regulations: list[Regulation]) -> list[RawChange]: ...
