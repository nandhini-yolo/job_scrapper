# job_scrapper

Daily monitoring for senior Python and data engineering roles in London and
Amsterdam that explicitly mention visa sponsorship or relocation support.

## Run locally

```bash
python -m pip install -r requirements.txt
python scraper.py
```

DRW and all currently verified public Greenhouse/Lever boards in the target
company registry are monitored by default. Add other public ATS boards and
career feeds without editing code:

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
comma-separated board IDs or URLs. The full target list is in
`job_scraper/companies.py`; firms with custom career systems remain listed
there until a stable public feed or site-specific adapter is verified.

## GitHub Pages dashboard

The `Publish job dashboard` workflow renders `jobs_cache.json` as a static
dashboard with direct application links. In repository settings, enable
**Pages** with **GitHub Actions** as the source. The dashboard is published
after a successful daily digest and also on pushes to `main`.
