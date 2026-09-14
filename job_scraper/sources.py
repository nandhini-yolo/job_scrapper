from __future__ import annotations

import json
import logging
import re
from typing import Any, Iterable
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from .companies import VERIFIED_GREENHOUSE_BOARDS, VERIFIED_LEVER_BOARDS
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
            yield Job(str(item.get("id")), item.get("title", ""), VERIFIED_GREENHOUSE_BOARDS.get(token, token), item.get("location", {}).get("name", ""), clean_html(item.get("content", "")), item.get("absolute_url", ""), self.name, item.get("updated_at"))


class LeverSource(JobSource):
    name = "Lever"

    def fetch(self, board: str) -> Iterable[Job]:
        token = urlparse(board).path.rstrip("/").split("/")[-1] if "://" in board else board
        payload = self.request_json(f"https://api.lever.co/v0/postings/{token}?mode=json")
        for item in payload if isinstance(payload, list) else []:
            categories = item.get("categories", {})
            yield Job(str(item.get("id")), item.get("text", ""), VERIFIED_LEVER_BOARDS.get(token, token), categories.get("location", ""), clean_html(item.get("descriptionPlain", item.get("description", ""))), item.get("hostedUrl", item.get("applyUrl", "")), self.name, item.get("createdAt"))


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


class CustomCareerSource(JobSource):
    """Best-effort scraper for public career pages without a known ATS API.

    It follows only a small number of same-domain links that look like job
    detail pages and prefers schema.org JobPosting data when available.
    Career sites rendered entirely by JavaScript may require a site-specific
    adapter or browser automation and are logged rather than guessed.
    """

    name = "Custom careers"
    LINK_TERMS = ("job", "career", "position", "opening", "vacanc", "apply", "role")
    MAX_DETAIL_PAGES = 40

    def fetch(self, company: str, market: str, url: str) -> Iterable[Job]:
        response = self.request_text(url)
        base_host = urlparse(response.url).netloc
        seen = {response.url}
        for job in self.schema_jobs(response.text, company, response.url):
            yield job
        soup = BeautifulSoup(response.text, "lxml")
        links = []
        for anchor in soup.find_all("a", href=True):
            href = urljoin(response.url, anchor["href"])
            label = f"{anchor.get_text(' ', strip=True)} {href}".lower()
            if urlparse(href).netloc != base_host or href in seen or not any(term in label for term in self.LINK_TERMS):
                continue
            links.append(href)
            if len(links) >= self.MAX_DETAIL_PAGES:
                break
        for detail_url in links:
            seen.add(detail_url)
            try:
                detail = self.request_text(detail_url)
            except requests.RequestException as exc:
                LOG.debug("Custom career detail %s failed: %s", detail_url, exc)
                continue
            schema_jobs = list(self.schema_jobs(detail.text, company, detail_url))
            if schema_jobs:
                yield from schema_jobs
                continue
            detail_soup = BeautifulSoup(detail.text, "lxml")
            title = detail_soup.find("h1") or detail_soup.find("title")
            if not title:
                continue
            description = clean_html(detail_soup.get_text(" ", strip=True))
            yield Job(detail_url, title.get_text(" ", strip=True), company, market, description, detail_url, self.name)

    def schema_jobs(self, text: str, company: str, source_url: str) -> Iterable[Job]:
        soup = BeautifulSoup(text, "lxml")
        for script in soup.select('script[type="application/ld+json"]'):
            try:
                payload = json.loads(script.string or script.get_text())
            except (TypeError, json.JSONDecodeError):
                continue
            records = payload if isinstance(payload, list) else [payload]
            for item in records:
                if item.get("@type") != "JobPosting":
                    continue
                organization = item.get("hiringOrganization", {})
                location = item.get("jobLocation", item.get("applicantLocationRequirements", ""))
                yield Job(str(item.get("url", source_url)), item.get("title", ""), organization.get("name", company), json.dumps(location), clean_html(item.get("description", "")), str(item.get("url", source_url)), self.name, item.get("datePosted"))


class EFinancialCareersSource(JobSource):
    name = "eFinancialCareers"

    def fetch(self, search_url: str) -> Iterable[Job]:
        response = self.request_text(search_url)
        soup = BeautifulSoup(response.text, "lxml")
        links = []
        for anchor in soup.find_all("a", href=True):
            href = urljoin(response.url, anchor["href"])
            if "/jobs-" not in href or any(href == existing[0] for existing in links):
                continue
            links.append((href, anchor.get_text(" ", strip=True)))
        for detail_url, listing_title in links[:50]:
            try:
                detail = self.request_text(detail_url)
            except requests.RequestException as exc:
                LOG.debug("eFinancialCareers detail %s failed: %s", detail_url, exc)
                if listing_title and listing_title.lower() not in {"apply", "apply now"}:
                    yield Job(detail_url, listing_title, "eFinancialCareers listing", self.location_from_url(detail_url), "Description unavailable from public listing page", detail_url, self.name)
                continue
            detail_soup = BeautifulSoup(detail.text, "lxml")
            title_node = detail_soup.find("h1") or detail_soup.find("title")
            if not title_node:
                if listing_title and listing_title.lower() not in {"apply", "apply now"}:
                    yield Job(detail_url, listing_title, "eFinancialCareers listing", self.location_from_url(detail_url), "Description unavailable from public listing page", detail_url, self.name)
                continue
            title = title_node.get_text(" ", strip=True)
            if title.lower().startswith("the personal information protection law"):
                if listing_title and listing_title.lower() not in {"apply", "apply now"}:
                    yield Job(detail_url, listing_title, "eFinancialCareers listing", self.location_from_url(detail_url), "Description unavailable from public listing page", detail_url, self.name)
                continue
            text = detail_soup.get_text(" ", strip=True)
            company = self.extract_label(text, "Company") or "eFinancialCareers listing"
            location = self.extract_label(text, "Location") or self.location_from_url(detail_url)
            yield Job(detail_url, title, company, location, text, detail_url, self.name)

    @staticmethod
    def extract_label(text: str, label: str) -> str:
        match = re.search(rf"{label}\s*[:\-]\s*([^|\n]+)", text, re.IGNORECASE)
        return match.group(1).strip() if match else ""

    @staticmethod
    def location_from_url(url: str) -> str:
        lowered = url.lower()
        if "amsterdam" in lowered:
            return "Amsterdam, Netherlands"
        if "london" in lowered:
            return "London, United Kingdom"
        return ""


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
    custom, finance = CustomCareerSource(settings.request_timeout), EFinancialCareersSource(settings.request_timeout)
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
    for company, market, url in settings.custom_career_pages:
        try:
            jobs.extend(custom.fetch(company, market, url))
        except requests.RequestException as exc:
            LOG.warning("%s page %s failed: %s", company, url, exc)
    for url in settings.finance_job_pages:
        try:
            jobs.extend(finance.fetch(url))
        except requests.RequestException as exc:
            LOG.warning("%s page %s failed: %s", finance.name, url, exc)
    return jobs