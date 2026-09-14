from __future__ import annotations

import argparse
import html
from datetime import datetime, timedelta, timezone
from pathlib import Path

from .cache import load
from .details import experience_required, technology_stack
from .interviews import interview_profile
from .models import Job


def as_jobs(cache: dict) -> list[Job]:
    jobs = []
    for record in cache.get("jobs", {}).values():
        try:
            jobs.append(Job(**{field: record.get(field, "") for field in Job.__dataclass_fields__}))
        except TypeError:
            continue
    return jobs


def is_new(job: Job) -> bool:
    try:
        return datetime.fromisoformat(job.first_seen) >= datetime.now(timezone.utc) - timedelta(hours=24)
    except (TypeError, ValueError):
        return False


def render(cache: dict) -> str:
    jobs = sorted(as_jobs(cache), key=lambda job: job.first_seen, reverse=True)
    new_jobs = [job for job in jobs if is_new(job)]
    active_jobs = [job for job in jobs if not is_new(job)]

    def cards(items: list[Job]) -> str:
        if not items:
            return '<p class="empty">No matching roles in this category yet.</p>'
        return "".join(
            f'<article class="job"><div><span class="company">{html.escape(job.company or "Company")}</span>'
            f'<h3>{html.escape(job.title)}</h3><p>{html.escape(job.location or "Location not listed")}</p>'
            f'<p><strong>Experience:</strong> {html.escape(experience_required(job))}</p>'
            f'<p><strong>Technology:</strong> {html.escape(technology_stack(job))}</p></div>'
            f'<div class="meta"><span class="tag">{job.country_tag}</span>'
            f'<span class="tag">Interview: {html.escape(interview_profile(job).label)} ({interview_profile(job).difficulty}/5)</span>'
            f'<span class="tag">{html.escape(job.source)}</span>'
            f'<a class="apply" href="{html.escape(job.url, quote=True)}" rel="noreferrer">Apply</a></div></article>'
            for job in items
        )

    updated = html.escape(str(cache.get("updated_at") or "Not run yet"))
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>London / Amsterdam Job Monitor</title><style>
:root {{ color-scheme: dark; --ink:#f4f1ea; --muted:#a9aaa4; --line:#303735; --accent:#e7ff62; --panel:#151b1a; --bg:#0b0f0e; }}
* {{ box-sizing:border-box; }} body {{ margin:0; background:var(--bg); color:var(--ink); font:16px/1.5 Georgia,serif; }}
main {{ max-width:1040px; margin:0 auto; padding:48px 22px 80px; }} header {{ border-bottom:1px solid var(--line); padding-bottom:34px; margin-bottom:38px; }}
.eyebrow,.company {{ color:var(--accent); font:700 12px/1.2 Arial,sans-serif; letter-spacing:.12em; text-transform:uppercase; }}
h1 {{ max-width:700px; margin:14px 0; font-size:clamp(38px,7vw,76px); line-height:.98; font-weight:400; }}
.intro,.updated {{ color:var(--muted); font-family:Arial,sans-serif; }} .intro {{ max-width:650px; font-size:18px; }}
.updated {{ font-size:12px; margin-top:26px; }} section {{ margin-top:42px; }} h2 {{ font-size:28px; font-weight:400; margin-bottom:16px; }}
.job {{ display:flex; justify-content:space-between; gap:24px; border-top:1px solid var(--line); padding:20px 0; }} h3 {{ margin:7px 0 5px; font-size:22px; font-weight:400; }} .job p {{ color:var(--muted); margin:0; font-family:Arial,sans-serif; font-size:14px; }}
.meta {{ display:flex; align-items:center; justify-content:flex-end; gap:8px; flex-wrap:wrap; min-width:220px; height:max-content; }} .tag {{ border:1px solid var(--line); color:var(--muted); padding:5px 8px; font:12px Arial,sans-serif; }}
.apply {{ background:var(--accent); color:#10130e; padding:7px 12px; text-decoration:none; font:700 13px Arial,sans-serif; }} .empty {{ color:var(--muted); border-top:1px solid var(--line); padding-top:20px; }}
@media(max-width:650px) {{ main {{ padding-top:30px; }} .job {{ display:block; }} .meta {{ justify-content:flex-start; margin-top:15px; min-width:0; }} }}
</style></head><body><main><header><div class="eyebrow">Career intelligence · India to Europe</div><h1>Senior Python &amp; data roles in London and Amsterdam.</h1><p class="intro">A live shortlist from public company career feeds, ranked for your engineering background. Sponsorship still needs to be confirmed with each employer.</p><p class="updated">Last scraper update: {updated}</p></header>
<section><h2>New in the last 24 hours <span class="eyebrow">{len(new_jobs)}</span></h2>{cards(new_jobs)}</section><section><h2>Active roles <span class="eyebrow">{len(active_jobs)}</span></h2>{cards(active_jobs)}</section></main></body></html>'''


def main() -> None:
    parser = argparse.ArgumentParser(description="Render the job cache as a static dashboard")
    parser.add_argument("--cache", type=Path, default=Path("jobs_cache.json"))
    parser.add_argument("--output", type=Path, default=Path("_site/index.html"))
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(render(load(args.cache)), encoding="utf-8")


if __name__ == "__main__":
    main()