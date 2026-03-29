"""Base regulation definition."""

from dataclasses import dataclass, field


@dataclass
class Regulation:
    id: str
    name: str
    celex_ids: list[str] = field(default_factory=list)
    eurovoc_codes: list[str] = field(default_factory=list)
    keywords: list[str] = field(default_factory=list)
    esma_tags: list[str] = field(default_factory=list)
    eba_tags: list[str] = field(default_factory=list)
