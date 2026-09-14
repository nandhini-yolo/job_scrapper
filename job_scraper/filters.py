from __future__ import annotations

import re

from .models import Job

SKILL_TERMS = ("python", "data engineer", "data engineering", "market data", "real-time data", "pyspark", "polars", "pandas", "pyarrow", "sql", "kafka", "airflow", "distributed systems", "data warehouse", "data warehousing", "data pipeline", "data pipelines", "etl", "elt", "clickhouse", "observability", "exchange feed", "trading systems")
SENIORITY_TERMS = ("senior", "lead", "staff", "principal", "architect", "9+ years", "10+ years")
LOCATION_TERMS = ("london", "united kingdom", " uk ", "amsterdam", "netherlands", " nl ")
VISA_TERMS = ("visa sponsorship", "visa sponsor", "relocation offered", "relocation package", "highly skilled migrant", "work permit", "sponsorship available", "skilled worker visa", "overseas candidates", "sponsor a visa", "sponsoring visa")
ROLE_TITLE_TERMS = ("data engineer", "data engineering", "market data", "data platform", "data infrastructure", "data pipeline", "data architect", "analytics engineer", "python engineer", "python developer", "ml platform", "machine learning platform", "trading systems", "quantitative developer", "quant technologist", "real-time data", "observability platform", "distributed systems")
MIN_MATCH_SCORE = 0.65
CATEGORY_DATA = "Data Engineering"
CATEGORY_PYTHON = "Python Software Engineering"
CATEGORY_PLATFORM = "Data Platform Engineering"


def has_seniority_signal(job: Job) -> bool:
    role_text = f"{job.title} {job.location}".lower()
    seniority_words = r"\b(?:senior|lead|staff|principal|architect)\b"
    return bool(re.search(seniority_words, role_text) or re.search(r"\b(?:9|10|11|12|13|14|15)\+?\s+years?\b", job.text))


def has_target_role_title(job: Job) -> bool:
    return role_category(job) is not None


def role_category(job: Job) -> str | None:
    title = job.title.lower()
    text = job.text
    if any(term in title for term in ("data platform", "data infrastructure", "ml platform", "machine learning platform", "platform engineer", "infrastructure engineer", "storage engineer", "observability platform", "distributed systems")):
        return CATEGORY_PLATFORM
    if any(term in title for term in ("data engineer", "data engineering", "market data", "analytics engineer", "data pipeline", "data warehouse", "data scientist")) or (" data" in title and "engineer" in title):
        return CATEGORY_DATA
    if any(term in title for term in ("python software engineer", "python engineer", "python developer", "quantitative developer", "quant technologist", "trading systems", "real-time data")):
        return CATEGORY_PYTHON
    if "software engineer" in title and any(term in text for term in ("python", "data pipeline", "data engineering", "data platform")):
        return CATEGORY_PYTHON
    return None


def match_score(job: Job) -> float:
    text = job.text
    role_text = f"{job.title} {job.location}".lower()
    has_seniority = has_seniority_signal(job)
    score = 0.0
    score += 0.35 if any(term in text for term in SKILL_TERMS) else 0.0
    score += 0.35 if any(term in role_text for term in LOCATION_TERMS) else 0.0
    score += 0.15 if has_seniority else 0.0
    score += 0.15 if any(term in text for term in VISA_TERMS) else 0.0
    return score


def has_visa_signal(job: Job) -> bool:
    analysis = job.analysis if isinstance(job.analysis, dict) else {}
    visa_status = f'{analysis.get("visa_status", "")} {analysis.get("relocation_status", "")}'.lower()
    return any(term in job.text for term in VISA_TERMS) or any(term in visa_status for term in ("yes", "supported", "available", "sponsor", "offered"))


def matches(job: Job) -> bool:
    text = job.text
    role_text = f"{job.title} {job.location}".lower()
    has_skill = any(term in text for term in SKILL_TERMS)
    has_location = any(term in role_text for term in LOCATION_TERMS)
    return has_target_role_title(job) and has_skill and has_location and has_seniority_signal(job) and match_score(job) >= MIN_MATCH_SCORE