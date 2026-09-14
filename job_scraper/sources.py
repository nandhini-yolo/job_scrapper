from __future__ import annotations

import json
import logging
from typing import Any, Iterable
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

from .models import Job

LOG = logging.getLogger(__name__)


class JobSource:
    name = "source"

    def __init__(self, timeout: int = 30) -> None:
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "job-scrapper/1.0", "Accept": "application/json, text/html;q=0.9, */*;q=0.8"})
        self.timeout = timeout

    def request_json(self, url: str) -> Any:
        response = self.session.get(url, timeout=self.timeout)
        response.raise_for_status()
        return response.json()

    def request_text(self, url: str) -> requests.Response:
        response = self.session.get(url, timeout=self.timeout)
        response.raise_for_status()
        return response


class GreenhouseSource(JobSource):
    name = "Greenhouse"

    def fetch(self, board: str) -> Iterable[Job]:
        token = urlparse(board).path.rstrip("/").split("/")[-1] if "://" in board else board
        payload = self.request_json(f"https://boards-api.greenhouse.io/v1/boards/{token}/jobs?content=true")
        for item in payload.get("jobs", []):
            yield Job(str(item.get("id")), item.get("title", ""), token, item.get("location", {}).get("name", ""), clean_html(item.get("content", "")), item.get("absolute_url", ""), self.name, item.get("updated_at"))


class LeverSource(JobSource):
    name = "Lever"

    def fetch(self, board: str) -> Iterable[Job]:
        token = urlparse(board).path.rstrip("/").split("/")[-1] if "://" in board else board
        payload = self.request_json(f"https://api.lever.co/v0/postings/{token}?mode=json")
        for item in payload if isinstance(payload, list) else []:
            categories = item.get("categories", {})
            yield Job(str(item.get("id")), item.get("text", ""), token, categories.get("location", ""), clean_html(item.get("descriptionPlain", item.get("description", ""))), item.get("hostedUrl", item.get("applyUrl", "")), self.name, item.get("createdAt"))


class FeedSource(JobSource):
    name = "Job feed"

    def fetch(self, url: str) -> Iterable[Job]:
        response = self.request_text(url)
        if "json" in response.headers.get("content-type", "") or url.lower().endswith(".json"):
            payload = response.json()
            items = payload.get("jobs", payload.get("results", payload.get("data", payload))) if isinstance(payload, dict) else payload
            for item in items if isinstance(items, list) else []:
                job = generic_job(item, urlparse(url).netloc)
                if job:
                    yield job
            return
        soup = BeautifulSoup(response.text, "lxml")
        for script in soup.select('script[type="application/ld+json"]'):
            try:
                payload = json.loads(script.string or script.get_text())
            except (TypeError, json.JSONDecodeError):
                continue
            for item in payload if isinstance(payload, list) else [payload]:
                if item.get("@type") == "JobPosting":
                    job = generic_job({"id": item.get("url"), "title": item.get("title"), "company": item.get("hiringOrganization", {}).get("name", ""), "location": json.dumps(item.get("jobLocation", "")), "description": item.get("description", ""), "url": item.get("url"), "posted_at": item.get("datePosted")}, urlparse(url).netloc)
                    if job:
                        yield job


def clean_html(value: Any) -> str:
    return BeautifulSoup(str(value or ""), "lxml").get_text(" ", strip=True)


def generic_job(item: dict[str, Any], source: str) -> Job | None:
    title = str(item.get("title", item.get("name", "")))
    url = str(item.get("url", item.get("apply_url", item.get("link", ""))))
    if not title or not url:
        return None
    return Job(str(item.get("id", url)), title, str(item.get("company", item.get("company_name", ""))), str(item.get("location", item.get("locations", ""))), clean_html(item.get("description", item.get("snippet", ""))), url, source, str(item.get("posted_at", item.get("date", item.get("created_at", "")))) or None)


def discover(settings: Any) -> list[Job]:
    jobs: list[Job] = []
    greenhouse, lever, feeds = GreenhouseSource(settings.request_timeout), LeverSource(settings.request_timeout), FeedSource(settings.request_timeout)
    for board in settings.greenhouse_boards:
        try:
            jobs.extend(greenhouse.fetch(board))
        except requests.RequestException as exc:
            LOG.warning("%s board %s failed: %s", greenhouse.name, board, exc)
    for board in settings.lever_boards:
        try:
            jobs.extend(lever.fetch(board))
        except requests.RequestException as exc:
            LOG.warning("%s board %s failed: %s", lever.name, board, exc)
    for url in settings.all_feeds:
        try:
            jobs.extend(feeds.fetch(url))
        except (requests.RequestException, ValueError) as exc:
            LOG.warning("Feed %s failed: %s", url, exc)
    return jobs