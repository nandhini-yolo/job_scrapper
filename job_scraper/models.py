from __future__ import annotations

from dataclasses import dataclass


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

    @property
    def text(self) -> str:
        return f"{self.title} {self.location} {self.description}".lower()

    @property
    def country_tag(self) -> str:
        return "🇬🇧 London" if any(term in self.text for term in ("london", "united kingdom", " uk ")) else "🇳🇱 Amsterdam"