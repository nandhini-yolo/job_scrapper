from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from .companies import VERIFIED_GREENHOUSE_BOARDS, VERIFIED_LEVER_BOARDS


def split_env(name: str) -> list[str]:
    return [value.strip() for value in os.getenv(name, "").split(",") if value.strip()]


def int_env(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, "") or default)
    except ValueError:
        return default


@dataclass(frozen=True)
class Settings:
    cache_path: Path = field(default_factory=lambda: Path(os.getenv("JOBS_CACHE", "jobs_cache.json")))
    request_timeout: int = field(default_factory=lambda: int_env("REQUEST_TIMEOUT", 30))
    greenhouse_boards: tuple[str, ...] = field(default_factory=lambda: tuple([*VERIFIED_GREENHOUSE_BOARDS, *split_env("GREENHOUSE_BOARDS")]))
    lever_boards: tuple[str, ...] = field(default_factory=lambda: tuple([*VERIFIED_LEVER_BOARDS, *split_env("LEVER_BOARDS")]))
    workday_feeds: tuple[str, ...] = field(default_factory=lambda: tuple(split_env("WORKDAY_FEEDS")))
    job_feeds: tuple[str, ...] = field(default_factory=lambda: tuple(split_env("JOB_FEEDS")))
    llm_provider: str = field(default_factory=lambda: os.getenv("LLM_PROVIDER", "gemini" if os.getenv("GEMINI_API_KEY") else ""))
    llm_model: str = field(default_factory=lambda: os.getenv("LLM_MODEL") or "gemini-2.0-flash-lite")
    llm_api_key: str = field(default_factory=lambda: os.getenv("GEMINI_API_KEY", ""))
    llm_max_jobs: int = field(default_factory=lambda: int_env("LLM_MAX_JOBS", 25))

    @property
    def all_feeds(self) -> tuple[str, ...]:
        return ("https://www.arbeitnow.com/api/job-board-api", *self.job_feeds, *self.workday_feeds)


def load_settings() -> Settings:
    settings = Settings()
    return Settings(cache_path=settings.cache_path, request_timeout=settings.request_timeout, greenhouse_boards=tuple(dict.fromkeys(settings.greenhouse_boards)), lever_boards=tuple(dict.fromkeys(settings.lever_boards)), workday_feeds=tuple(dict.fromkeys(settings.workday_feeds)), job_feeds=tuple(dict.fromkeys(settings.job_feeds)), llm_provider=settings.llm_provider, llm_model=settings.llm_model, llm_api_key=settings.llm_api_key, llm_max_jobs=settings.llm_max_jobs)