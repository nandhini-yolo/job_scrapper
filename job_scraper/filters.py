from __future__ import annotations

import re

from .models import Job

SKILL_TERMS = ("python", "data engineer", "data engineering", "pyspark", "polars", "pandas", "sql", "kafka", "airflow", "distributed systems", "data warehouse", "data warehousing", "data pipeline", "data pipelines", "etl", "elt")
SENIORITY_TERMS = ("senior", "lead", "staff", "principal", "architect", "9+ years", "10+ years")
LOCATION_TERMS = ("london", "united kingdom", " uk ", "amsterdam", "netherlands", " nl ")
VISA_TERMS = ("visa sponsorship", "visa sponsor", "relocation offered", "relocation package", "highly skilled migrant", "work permit", "sponsorship available", "skilled worker visa", "overseas candidates", "sponsor a visa", "sponsoring visa")
MIN_MATCH_SCORE = 0.65


def has_seniority_signal(job: Job) -> bool:
    role_text = f"{job.title} {job.location}".lower()
    seniority_words = r"\b(?:senior|lead|staff|principal|architect)\b"
    return bool(re.search(seniority_words, role_text) or re.search(r"\b(?:9|10|11|12|13|14|15)\+?\s+years?\b", job.text))


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
    return any(term in job.text for term in VISA_TERMS)


def matches(job: Job) -> bool:
    text = job.text
    role_text = f"{job.title} {job.location}".lower()
    has_skill = any(term in text for term in SKILL_TERMS)
    has_location = any(term in role_text for term in LOCATION_TERMS)
    return has_skill and has_location and has_seniority_signal(job) and match_score(job) >= MIN_MATCH_SCORE