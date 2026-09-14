from __future__ import annotations

import logging

from .cache import load, update
from .config import load_settings
from .filters import matches
from .report import build_html, send_email
from .sources import discover

LOG = logging.getLogger("job-scraper")


def main() -> None:
    logging.basicConfig(level="INFO", format="%(levelname)s %(message)s")
    settings = load_settings()
    matching = {job.id: job for job in discover(settings) if matches(job)}
    new_jobs, active_jobs = update(settings.cache_path, list(matching.values()), load(settings.cache_path))
    try:
        send_email(build_html(new_jobs, active_jobs), len(new_jobs) + len(active_jobs), settings.request_timeout)
    except RuntimeError as exc:
        LOG.warning("%s; email skipped", exc)
    LOG.info("Processed %d matching jobs: %d new, %d active", len(matching), len(new_jobs), len(active_jobs))