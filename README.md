# job_scrapper

Daily monitoring for senior Python and data engineering roles in London and
Amsterdam that explicitly mention visa sponsorship or relocation support.

## Run locally

```bash
python -m pip install -r requirements.txt
python scraper.py
```

DRW (`drweng`) is monitored by default through Greenhouse. Add other public
ATS boards and career feeds without editing code:

```bash
export GREENHOUSE_BOARDS="company-a,company-b"
export LEVER_BOARDS="company-a,company-b"
export WORKDAY_FEEDS="https://company.example/jobs"
export JOB_FEEDS="https://company.example/jobs.json"
python scraper.py
```

The scraper stores state in `jobs_cache.json`. Configure the SMTP environment
variables used by the GitHub Actions workflow to receive the daily digest:
`SMTP_SERVER`, `SMTP_PORT`, `SENDER_EMAIL`, `SENDER_PASSWORD`, and
`RECIPIENT_EMAIL`. For scheduled runs, add repository **Variables** named
`GREENHOUSE_BOARDS`, `LEVER_BOARDS`, `WORKDAY_FEEDS`, and `JOB_FEEDS` with
comma-separated board IDs or URLs. DRW remains enabled by default.
