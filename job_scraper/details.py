from __future__ import annotations

import re

from .filters import SKILL_TERMS
from .models import Job

DISPLAY_SKILLS = {
    "python": "Python",
    "pyspark": "PySpark",
    "polars": "Polars",
    "pandas": "Pandas",
    "pyarrow": "PyArrow",
    "sql": "SQL",
    "kafka": "Kafka",
    "airflow": "Airflow",
    "distributed systems": "Distributed Systems",
    "data warehousing": "Data Warehousing",
    "data warehouse": "Data Warehousing",
    "data pipelines": "Data Pipelines",
    "data pipeline": "Data Pipelines",
    "etl": "ETL",
    "elt": "ELT",
    "clickhouse": "ClickHouse",
    "observability": "Observability",
    "market data": "Market Data",
    "exchange feed": "Exchange Feeds",
    "trading systems": "Trading Systems",
}


def experience_required(job: Job) -> str:
    analysis = job.analysis if isinstance(job.analysis, dict) else {}
    analyzed = str(analysis.get("required_years", "")).strip()
    if analyzed and analyzed.lower() not in {"unknown", "not stated", "none"}:
        return analyzed
    matches = re.findall(r"\b(?:minimum of |at least )?(\d+\+?)\s+years?\b", job.text)
    return ", ".join(dict.fromkeys(f"{value} years" for value in matches)) or "Not stated"


def technology_stack(job: Job) -> str:
    analysis = job.analysis if isinstance(job.analysis, dict) else {}
    analyzed = analysis.get("skills")
    if isinstance(analyzed, list) and analyzed:
        return ", ".join(str(skill) for skill in analyzed[:8])
    found = []
    for term in SKILL_TERMS:
        if term in job.text and term in DISPLAY_SKILLS and DISPLAY_SKILLS[term] not in found:
            found.append(DISPLAY_SKILLS[term])
    return ", ".join(found[:8]) or "Not stated"