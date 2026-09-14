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

The verified ATS registry also includes Schonfeld, Point72, Stripe, Cloudflare,
Monzo, Brex, Affirm, N26, Datadog, Reddit, GitLab, Lyft, and Coinbase. A
recent live run discovered 6,298 jobs and returned 34 focused senior roles
after applying the location, seniority, and profile-aligned filters.

Additional verified feeds include Tide, SumUp, Celonis, MongoDB, Fastly,
Twilio, Okta, Fivetran, GoCardless, TrueLayer, Graphcore, Wayve, Scale AI,
Veriff, Trustpilot, HelloFresh, commercetools, Contentsquare, and Zopa. The
registry currently covers 91 target companies and 45 public ATS boards.

Custom career-page crawling is enabled for registered hedge funds that do not
publish Greenhouse or Lever APIs. It follows same-domain job links and reads
schema.org `JobPosting` data where available. A smoke test extracted public
listings from D. E. Shaw, Two Sigma, Hudson River Trading, SIG, Tower Research,
Virtu, Brevan Howard, G-Research, and XTX Markets. JavaScript-only pages or
changed URLs are logged for later site-specific adapters; they are not treated
as confirmed coverage.

Optional job-description analysis can use Gemini's free quota. Add the
`GEMINI_API_KEY` repository secret and set `LLM_PROVIDER=gemini` as a
repository variable. Optional variables are `LLM_MODEL` and `LLM_MAX_JOBS`.
The default is disabled; local Ollama is also supported with
`LLM_PROVIDER=ollama`.

If `LLM_MODEL` is missing or no longer available, the scraper queries Gemini's
model list and selects a usable `generateContent` Flash or Pro model
automatically. Gemini API keys are sent in request headers, not URLs.

### Local Gemini run

The key is read only from the process environment and is never written to
the repository. In a local terminal:

```bash
export GEMINI_API_KEY="paste-your-key-here"
export LLM_PROVIDER=gemini
python scraper.py
unset GEMINI_API_KEY LLM_PROVIDER
```

Without `GEMINI_API_KEY`, the scraper automatically skips LLM analysis and
continues with deterministic matching. Do not place the key in source files,
`jobs_cache.json`, or committed workflow variables.

Interview difficulty and required-skill details are shown per role. The
interview rating is a planning estimate from the company type and role scope,
not a guaranteed pass probability; interview loops vary by team and change
over time. The report shows a 1/5 to 5/5 scale, expected stages, and skills to
prepare.

## GitHub Pages dashboard

The `Publish job dashboard` workflow renders `jobs_cache.json` as a static
dashboard with direct application links. In repository settings, enable
**Pages** with **GitHub Actions** as the source. The dashboard is published
after a successful daily digest and also on pushes to `main`.
