from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


def split_env(name: str) -> list[str]:
    return [value.strip() for value in os.getenv(name, "").split(",") if value.strip()]


@dataclass(frozen=True)
class Settings:
    cache_path: Path = field(default_factory=lambda: Path(os.getenv("JOBS_CACHE", "jobs_cache.json")))
    request_timeout: int = field(default_factory=lambda: int(os.getenv("REQUEST_TIMEOUT", "30")))
    greenhouse_boards: tuple[str, ...] = field(default_factory=lambda: tuple(["drweng"] + split_env("GREENHOUSE_BOARDS")))
    lever_boards: tuple[str, ...] = field(default_factory=lambda: tuple(split_env("LEVER_BOARDS")))
    workday_feeds: tuple[str, ...] = field(default_factory=lambda: tuple(split_env("WORKDAY_FEEDS")))
    job_feeds: tuple[str, ...] = field(default_factory=lambda: tuple(split_env("JOB_FEEDS")))

    @property
    def all_feeds(self) -> tuple[str, ...]:
        return ("https://www.arbeitnow.com/api/job-board-api", *self.job_feeds, *self.workday_feeds)


def load_settings() -> Settings:
    settings = Settings()
    return Settings(cache_path=settings.cache_path, request_timeout=settings.request_timeout, greenhouse_boards=tuple(dict.fromkeys(settings.greenhouse_boards)), lever_boards=tuple(dict.fromkeys(settings.lever_boards)), workday_feeds=tuple(dict.fromkeys(settings.workday_feeds)), job_feeds=tuple(dict.fromkeys(settings.job_feeds)))