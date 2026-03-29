"""Registry for regulations and sources."""

from regwatch.regulations import ALL_REGULATIONS
from regwatch.regulations.base import Regulation
from regwatch.sources import ALL_SOURCES


def get_regulations() -> list[Regulation]:
    """Return all registered regulation definitions."""
    return list(ALL_REGULATIONS)


def get_sources() -> list:
    """Return all registered source instances."""
    return list(ALL_SOURCES)
