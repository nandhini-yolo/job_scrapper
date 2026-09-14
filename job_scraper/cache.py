from __future__ import annotations

import json
import logging
from dataclasses import asdict, fields
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from .models import Job

LOG = logging.getLogger(__name__)


def now() -> datetime:
    return datetime.now(timezone.utc)


def load(path: Path) -> dict[str, Any]:
    if not path.exists() or path.stat().st_size == 0:
        return {"updated_at": None, "jobs": {}}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        return payload if isinstance(payload.get("jobs"), dict) else {"updated_at": None, "jobs": {}}
    except (OSError, json.JSONDecodeError) as exc:
        LOG.warning("Could not read cache: %s", exc)
        return {"updated_at": None, "jobs": {}}


def update(path: Path, jobs: list[Job], cache: dict[str, Any]) -> tuple[list[Job], list[Job]]:
    timestamp = now().isoformat()
    records = cache.setdefault("jobs", {})
    for job in jobs:
        previous = records.get(job.id, {})
        job.first_seen = previous.get("first_seen", timestamp)
        job.last_seen = timestamp
        records[job.id] = asdict(job)
    cache["updated_at"] = timestamp
    path.write_text(json.dumps(cache, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    cutoff = now() - timedelta(hours=24)
    new_jobs, active_jobs = [], []
    valid_fields = {field.name for field in fields(Job)}
    for record in records.values():
        try:
            first_seen = datetime.fromisoformat(record["first_seen"])
            job = Job(**{key: record.get(key, {} if key == "analysis" else "") for key in valid_fields})
        except (KeyError, TypeError, ValueError):
            continue
        (new_jobs if first_seen >= cutoff else active_jobs).append(job)
    return new_jobs, active_jobs