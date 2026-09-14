from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Job:
    id: str
    title: str
    company: str
    location: str
    description: str
    url: str
    source: str
    posted_at: str | None = None
    first_seen: str = ""
    last_seen: str = ""
    analysis: dict[str, Any] = field(default_factory=dict)

    @property
    def text(self) -> str:
        return f"{self.title} {self.location} {self.description}".lower()

    @property
    def country_tag(self) -> str:
        return "🇬🇧 London" if any(term in self.text for term in ("london", "united kingdom", " uk ")) else "🇳🇱 Amsterdam"