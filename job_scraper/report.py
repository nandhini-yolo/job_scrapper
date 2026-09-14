from __future__ import annotations

import html
import os
import smtplib
from email.message import EmailMessage
from email.utils import format_datetime

from .cache import now
from .details import experience_required, technology_stack
from .filters import CATEGORY_DATA, CATEGORY_PLATFORM, CATEGORY_PYTHON, has_visa_signal, match_score, role_category
from .interviews import interview_profile
from .models import Job


def build_html(new_jobs: list[Job], active_jobs: list[Job]) -> str:
    def rows(jobs: list[Job]) -> str:
        if not jobs:
            return '<tr><td colspan="8">No matching roles in this category.</td></tr>'
        return "".join(f'<tr><td><a href="{html.escape(job.url, quote=True)}">{html.escape(job.title)}</a></td><td>{html.escape(job.company or "Unknown company")}</td><td>{job.country_tag}</td><td>{html.escape(experience_required(job))}</td><td>{html.escape(technology_stack(job))}</td><td>{html.escape(interview_profile(job).label)} ({interview_profile(job).difficulty}/5)</td><td>{"✈️ Visa/Relocation Signal" if has_visa_signal(job) else "⚠️ Verify Sponsorship"}</td><td>{html.escape(analysis_summary(job))}</td><td>{match_score(job):.0%}</td></tr>' for job in jobs)

    def analysis_summary(job: Job) -> str:
        analysis = job.analysis if isinstance(job.analysis, dict) else {}
        if not analysis:
            return "Keyword match"
        seniority = str(analysis.get("seniority", "Unknown"))
        years = str(analysis.get("required_years", "Unknown"))
        return f"{seniority}; {years}"
    sections = []
    for category in (CATEGORY_DATA, CATEGORY_PYTHON, CATEGORY_PLATFORM):
        category_new = [job for job in new_jobs if role_category(job) == category]
        category_active = [job for job in active_jobs if role_category(job) == category]
        sections.append(f'<section><h2>{html.escape(category)}</h2><h3>🆕 New in the last 24 hours</h3><table border="1" cellpadding="8" cellspacing="0"><tr><th>Role</th><th>Company</th><th>Location</th><th>Experience</th><th>Technology stack</th><th>Interview ease</th><th>Visa</th><th>AI analysis</th><th>Fit</th></tr>{rows(category_new)}</table><h3>📋 Active ongoing roles</h3><table border="1" cellpadding="8" cellspacing="0"><tr><th>Role</th><th>Company</th><th>Location</th><th>Experience</th><th>Technology stack</th><th>Interview ease</th><th>Visa</th><th>AI analysis</th><th>Fit</th></tr>{rows(category_active)}</table></section>')
    return f'''<!doctype html><html><body style="font-family:Arial,sans-serif;color:#17202a"><h1>Focused senior engineering roles</h1><p>Data Engineering → Python Software Engineering → Data Platform Engineering. Ranked by skills, location, seniority, and visa evidence. Confirm sponsorship with the employer.</p>{"".join(sections)}</body></html>'''


def send_email(body: str, total: int, timeout: int) -> None:
    required = ["SMTP_SERVER", "SENDER_EMAIL", "SENDER_PASSWORD", "RECIPIENT_EMAIL"]
    configured = [bool(os.getenv(name)) for name in required]
    if not any(configured):
        raise RuntimeError(f"SMTP is not configured; found {total} matching jobs")
    if not all(configured):
        raise RuntimeError("SMTP_SERVER, SMTP_PORT, SENDER_EMAIL, SENDER_PASSWORD, and RECIPIENT_EMAIL must be set together")
    message = EmailMessage()
    message["Subject"] = f"Daily job digest: {total} matching roles"
    message["From"] = os.environ["SENDER_EMAIL"]
    message["To"] = os.environ["RECIPIENT_EMAIL"]
    message["Date"] = format_datetime(now())
    message.set_content("Open this message in an HTML-capable email client.")
    message.add_alternative(body, subtype="html")
    with smtplib.SMTP(os.environ["SMTP_SERVER"], int(os.getenv("SMTP_PORT", "587")), timeout=timeout) as server:
        server.starttls()
        server.login(os.environ["SENDER_EMAIL"], os.environ["SENDER_PASSWORD"])
        server.send_message(message)