"""CLI entrypoint for the modular job scraper."""

from job_scraper.filters import matches
from job_scraper.models import Job
from job_scraper.runner import main

__all__ = ["Job", "matches", "main"]


if __name__ == "__main__":
    main()