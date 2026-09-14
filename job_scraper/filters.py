from __future__ import annotations

import re

from .models import Job

SKILL_TERMS = ("python", "data engineer", "data engineering", "pyspark", "polars", "pandas", "sql", "kafka", "airflow", "distributed systems", "data warehouse", "data warehousing", "data pipeline", "data pipelines", "etl", "elt")
SENIORITY_TERMS = ("senior", "lead", "staff", "principal", "architect", "9+ years", "10+ years")
LOCATION_TERMS = ("london", "united kingdom", " uk ", "amsterdam", "netherlands", " nl ")
VISA_TERMS = ("visa sponsorship", "visa sponsor", "relocation offered", "relocation package", "highly skilled migrant", "work permit", "sponsorship available", "skilled worker visa", "overseas candidates", "sponsor a visa", "sponsoring visa")


def matches(job: Job) -> bool:
    text = job.text
    has_seniority = any(term in text for term in SENIORITY_TERMS) or re.search(r"\b(?:9|10|11|12|13|14|15)\+?\s+years?\b", text)
    return bool(any(term in text for term in SKILL_TERMS) and has_seniority and any(term in text for term in LOCATION_TERMS) and any(term in text for term in VISA_TERMS))