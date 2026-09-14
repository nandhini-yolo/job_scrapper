from __future__ import annotations

import html
import os
import smtplib
from email.message import EmailMessage
from email.utils import format_datetime

from .cache import now
from .filters import has_visa_signal, match_score
from .models import Job


def build_html(new_jobs: list[Job], active_jobs: list[Job]) -> str:
    def rows(jobs: list[Job]) -> str:
        if not jobs:
            return '<tr><td colspan="4">No matching roles in this category.</td></tr>'
        return "".join(f'<tr><td><a href="{html.escape(job.url, quote=True)}">{html.escape(job.title)}</a></td><td>{html.escape(job.company or "Unknown company")}</td><td>{job.country_tag}</td><td>{"✈️ Visa/Relocation Signal" if has_visa_signal(job) else "⚠️ Verify Sponsorship"}</td><td>{match_score(job):.0%}</td></tr>' for job in jobs)
    return f'''<!doctype html><html><body style="font-family:Arial,sans-serif;color:#17202a"><h1>Senior Python &amp; Data Engineering roles</h1><p>Promising London / Amsterdam roles ranked by skills, location, seniority, and visa evidence. Confirm sponsorship with the employer.</p><h2>🆕 Newly Posted Jobs (last 24 hours)</h2><table border="1" cellpadding="8" cellspacing="0"><tr><th>Role</th><th>Company</th><th>Location</th><th>Visa</th><th>Fit</th></tr>{rows(new_jobs)}</table><h2>📋 Active Ongoing Roles</h2><table border="1" cellpadding="8" cellspacing="0"><tr><th>Role</th><th>Company</th><th>Location</th><th>Visa</th><th>Fit</th></tr>{rows(active_jobs)}</table></body></html>'''


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