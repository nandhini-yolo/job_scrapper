"""Discover and report senior Python/data engineering roles in the UK and NL.

Public ATS platforms do not expose one global unauthenticated company
directory. Configure board identifiers or feed URLs with environment
variables to extend discovery without changing this script:
GREENHOUSE_BOARDS=company-a,company-b, LEVER_BOARDS=company-a,company-b,
WORKDAY_FEEDS=https://example.com/careers/search, and JOB_FEEDS=url1,url2.
"""

from __future__ import annotations

import html
import json
import logging
import os
import re
import smtplib
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
from email.utils import format_datetime
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

LOG = logging.getLogger("job-scraper")
CACHE_PATH = Path(os.getenv("JOBS_CACHE", "jobs_cache.json"))
TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "30"))
SESSION = requests.Session()
SESSION.headers.update({"User-Agent": "job-scrapper/1.0", "Accept": "application/json, text/html;q=0.9, */*;q=0.8"})

SKILL_TERMS = ("python", "data engineer", "data engineering", "pyspark", "polars", "pandas", "sql", "kafka", "airflow", "distributed systems", "data warehouse", "data warehousing", "data pipeline", "data pipelines", "etl", "elt")
SENIORITY_TERMS = ("senior", "lead", "staff", "principal", "architect", "9+ years", "10+ years")
LOCATION_TERMS = ("london", "united kingdom", " uk ", "amsterdam", "netherlands", " nl ")
VISA_TERMS = ("visa sponsorship", "visa sponsor", "relocation offered", "relocation package", "highly skilled migrant", "work permit", "sponsorship available", "skilled worker visa", "overseas candidates", "sponsor a visa", "sponsoring visa")


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


def now() -> datetime:
    return datetime.now(timezone.utc)


def split_env(name: str) -> list[str]:
    return [value.strip() for value in os.getenv(name, "").split(",") if value.strip()]


def get_json(url: str) -> Any:
    response = SESSION.get(url, timeout=TIMEOUT)
    response.raise_for_status()
    return response.json()


def fetch_greenhouse(board: str) -> Iterable[Job]:
    token = urlparse(board).path.rstrip("/").split("/")[-1] if "://" in board else board
    payload = get_json(f"https://boards-api.greenhouse.io/v1/boards/{token}/jobs?content=true")
    for item in payload.get("jobs", []):
        yield Job(str(item.get("id")), item.get("title", ""), token, item.get("location", {}).get("name", ""), BeautifulSoup(item.get("content", ""), "lxml").get_text(" ", strip=True), item.get("absolute_url", ""), "Greenhouse", item.get("updated_at"))


def fetch_lever(board: str) -> Iterable[Job]:
    token = urlparse(board).path.rstrip("/").split("/")[-1] if "://" in board else board
    payload = get_json(f"https://api.lever.co/v0/postings/{token}?mode=json")
    for item in payload if isinstance(payload, list) else []:
        categories = item.get("categories", {})
        description = BeautifulSoup(item.get("descriptionPlain", item.get("description", "")), "lxml").get_text(" ", strip=True)
        yield Job(str(item.get("id")), item.get("text", ""), token, categories.get("location", ""), description, item.get("hostedUrl", item.get("applyUrl", "")), "Lever", item.get("createdAt"))


def parse_generic_item(item: dict[str, Any], source: str) -> Job | None:
    title = str(item.get("title", item.get("name", "")))
    url = str(item.get("url", item.get("apply_url", item.get("link", ""))))
    if not title or not url:
        return None
    return Job(str(item.get("id", url)), title, str(item.get("company", item.get("company_name", ""))), str(item.get("location", item.get("locations", ""))), BeautifulSoup(str(item.get("description", item.get("snippet", ""))), "lxml").get_text(" ", strip=True), url, source, str(item.get("posted_at", item.get("date", item.get("created_at", "")))) or None)


def fetch_feed(url: str) -> Iterable[Job]:
    response = SESSION.get(url, timeout=TIMEOUT)
    response.raise_for_status()
    content_type = response.headers.get("content-type", "")
    if "json" in content_type or url.lower().endswith(".json"):
        payload = response.json()
        items = payload.get("jobs", payload.get("results", payload.get("data", payload))) if isinstance(payload, dict) else payload
        for item in items if isinstance(items, list) else []:
            job = parse_generic_item(item, urlparse(url).netloc)
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
                job = parse_generic_item({"id": item.get("url"), "title": item.get("title"), "company": item.get("hiringOrganization", {}).get("name", ""), "location": json.dumps(item.get("jobLocation", "")), "description": item.get("description", ""), "url": item.get("url"), "posted_at": item.get("datePosted")}, urlparse(url).netloc)
                if job:
                    yield job


def discover() -> list[Job]:
    jobs: list[Job] = []
    for source, fetcher, boards in (("Greenhouse", fetch_greenhouse, split_env("GREENHOUSE_BOARDS")), ("Lever", fetch_lever, split_env("LEVER_BOARDS"))):
        for board in boards:
            try:
                jobs.extend(fetcher(board))
            except requests.RequestException as exc:
                LOG.warning("%s board %s failed: %s", source, board, exc)
    for url in ["https://www.arbeitnow.com/api/job-board-api"] + split_env("JOB_FEEDS") + split_env("WORKDAY_FEEDS"):
        try:
            jobs.extend(fetch_feed(url))
        except (requests.RequestException, ValueError) as exc:
            LOG.warning("Feed %s failed: %s", url, exc)
    return jobs


def matches(job: Job) -> bool:
    text = job.text
    has_seniority = any(term in text for term in SENIORITY_TERMS) or re.search(r"\b(?:9|10|11|12|13|14|15)\+?\s+years?\b", text)
    return bool(any(term in text for term in SKILL_TERMS) and has_seniority and any(term in text for term in LOCATION_TERMS) and any(term in text for term in VISA_TERMS))


def load_cache() -> dict[str, Any]:
    if not CACHE_PATH.exists():
        return {"updated_at": None, "jobs": {}}
    try:
        payload = json.loads(CACHE_PATH.read_text(encoding="utf-8"))
        return payload if isinstance(payload.get("jobs"), dict) else {"updated_at": None, "jobs": {}}
    except (OSError, json.JSONDecodeError) as exc:
        LOG.warning("Could not read cache: %s", exc)
        return {"updated_at": None, "jobs": {}}


def update_cache(jobs: list[Job], cache: dict[str, Any]) -> tuple[list[Job], list[Job]]:
    timestamp = now().isoformat()
    records = cache.setdefault("jobs", {})
    for job in jobs:
        previous = records.get(job.id, {})
        job.first_seen = previous.get("first_seen", timestamp)
        job.last_seen = timestamp
        records[job.id] = asdict(job)
    cache["updated_at"] = timestamp
    CACHE_PATH.write_text(json.dumps(cache, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    cutoff = now() - timedelta(hours=24)
    new_jobs, active_jobs = [], []
    for record in records.values():
        try:
            first_seen = datetime.fromisoformat(record["first_seen"])
        except (KeyError, ValueError):
            continue
        job = Job(**{key: record.get(key, "") for key in Job.__dataclass_fields__})
        (new_jobs if first_seen >= cutoff else active_jobs).append(job)
    return new_jobs, active_jobs


def build_email(new_jobs: list[Job], active_jobs: list[Job]) -> str:
    def rows(jobs: list[Job]) -> str:
        if not jobs:
            return '<tr><td colspan="4">No matching roles in this category.</td></tr>'
        return "".join(f'<tr><td><a href="{html.escape(job.url, quote=True)}">{html.escape(job.title)}</a></td><td>{html.escape(job.company or "Unknown company")}</td><td>{job.country_tag}</td><td>✈️ Visa Sponsored</td></tr>' for job in jobs)
    return f'''<!doctype html><html><body style="font-family:Arial,sans-serif;color:#17202a"><h1>Senior Python &amp; Data Engineering roles</h1><p>London / Amsterdam roles with explicit sponsorship or relocation language.</p><h2>🆕 Newly Posted Jobs (last 24 hours)</h2><table border="1" cellpadding="8" cellspacing="0"><tr><th>Role</th><th>Company</th><th>Location</th><th>Visa</th></tr>{rows(new_jobs)}</table><h2>📋 Active Ongoing Roles</h2><table border="1" cellpadding="8" cellspacing="0"><tr><th>Role</th><th>Company</th><th>Location</th><th>Visa</th></tr>{rows(active_jobs)}</table></body></html>'''


def send_email(body: str, total: int) -> None:
    required = ["SMTP_SERVER", "SENDER_EMAIL", "SENDER_PASSWORD", "RECIPIENT_EMAIL"]
    configured = [bool(os.getenv(name)) for name in required]
    if not any(configured):
        LOG.warning("SMTP is not configured; found %d matching jobs and skipped email.", total)
        return
    if not all(configured):
        raise RuntimeError("SMTP_SERVER, SENDER_EMAIL, SENDER_PASSWORD, and RECIPIENT_EMAIL must be set together")
    message = EmailMessage()
    message["Subject"] = f"Daily job digest: {total} matching roles"
    message["From"] = os.environ["SENDER_EMAIL"]
    message["To"] = os.environ["RECIPIENT_EMAIL"]
    message["Date"] = format_datetime(now())
    message.set_content("Open this message in an HTML-capable email client.")
    message.add_alternative(body, subtype="html")
    with smtplib.SMTP(os.environ["SMTP_SERVER"], int(os.getenv("SMTP_PORT", "587")), timeout=TIMEOUT) as server:
        server.starttls()
        server.login(os.environ["SENDER_EMAIL"], os.environ["SENDER_PASSWORD"])
        server.send_message(message)


def main() -> None:
    logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"), format="%(levelname)s %(message)s")
    matching = {job.id: job for job in discover() if matches(job)}
    new_jobs, active_jobs = update_cache(list(matching.values()), load_cache())
    send_email(build_email(new_jobs, active_jobs), len(new_jobs) + len(active_jobs))
    LOG.info("Processed %d matching jobs: %d new, %d active", len(matching), len(new_jobs), len(active_jobs))


if __name__ == "__main__":
    main()