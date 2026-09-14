from __future__ import annotations

import json
import logging
from typing import Any

import requests

from .models import Job

LOG = logging.getLogger(__name__)


def prompt_for(job: Job) -> str:
    return f'''Analyze this job description for a candidate with 9+ years building Python market-data and data-platform systems in quantitative trading.

Return JSON only with these keys: relevant, category, seniority, required_years, skills, location, visa_status, relocation_status, evidence, confidence.
Use only facts in the supplied text. `evidence` must contain exact short quotes from the description. Set visa_status or relocation_status to "unknown" when not explicitly stated.

TITLE: {job.title}
LOCATION: {job.location}
DESCRIPTION:
{job.description[:14000]}'''


def parse_json(text: str) -> dict[str, Any]:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("\n", 1)[1].rsplit("```", 1)[0]
    value = json.loads(cleaned)
    return value if isinstance(value, dict) else {}


def analyze_gemini(job: Job, api_key: str, model: str, timeout: int) -> dict[str, Any]:
    headers = {"x-goog-api-key": api_key}
    payload = {"contents": [{"parts": [{"text": prompt_for(job)}]}], "generationConfig": {"temperature": 0, "responseMimeType": "application/json"}}
    response = requests.post(f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent", headers=headers, json=payload, timeout=timeout)
    if response.status_code == 404:
        model = find_gemini_model(api_key, timeout, preferred=model)
        response = requests.post(f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent", headers=headers, json=payload, timeout=timeout)
    response.raise_for_status()
    text = response.json()["candidates"][0]["content"]["parts"][0]["text"]
    return parse_json(text)


def find_gemini_model(api_key: str, timeout: int, preferred: str = "") -> str:
    response = requests.get("https://generativelanguage.googleapis.com/v1beta/models", headers={"x-goog-api-key": api_key}, timeout=timeout)
    response.raise_for_status()
    candidates = []
    for item in response.json().get("models", []):
        name = str(item.get("name", "")).removeprefix("models/")
        methods = item.get("supportedGenerationMethods", [])
        if "generateContent" in methods and "gemini" in name.lower() and "embedding" not in name.lower():
            candidates.append(name)
    if preferred in candidates:
        return preferred
    for pattern in ("flash-lite", "flash", "pro"):
        for name in candidates:
            if pattern in name.lower():
                LOG.info("Using available Gemini model %s", name)
                return name
    if candidates:
        LOG.info("Using available Gemini model %s", candidates[0])
        return candidates[0]
    raise RuntimeError("Gemini API returned no usable generateContent model")


def analyze_ollama(job: Job, model: str, timeout: int) -> dict[str, Any]:
    response = requests.post("http://localhost:11434/api/generate", json={"model": model, "prompt": prompt_for(job), "format": "json", "stream": False}, timeout=timeout)
    response.raise_for_status()
    return parse_json(response.json().get("response", "{}"))


def enrich_jobs(jobs: list[Job], settings: Any) -> None:
    provider = settings.llm_provider.lower().strip()
    if not provider:
        return
    if provider == "gemini" and not settings.llm_api_key:
        LOG.warning("LLM_PROVIDER=gemini but GEMINI_API_KEY is missing; LLM analysis skipped")
        return
    model = settings.llm_model
    try:
        if provider == "gemini":
            model = find_gemini_model(settings.llm_api_key, settings.request_timeout, settings.llm_model)
    except (requests.RequestException, RuntimeError) as exc:
        LOG.warning("Gemini model discovery failed: %s; LLM analysis skipped", exc)
        return
    for job in jobs[: settings.llm_max_jobs]:
        try:
            if provider == "gemini":
                job.analysis = analyze_gemini(job, settings.llm_api_key, model, settings.request_timeout)
            elif provider == "ollama":
                job.analysis = analyze_ollama(job, settings.llm_model, settings.request_timeout)
            else:
                LOG.warning("Unsupported LLM_PROVIDER=%s; analysis skipped", provider)
                return
        except (requests.RequestException, KeyError, TypeError, ValueError, RuntimeError) as exc:
            LOG.warning("LLM analysis failed for %s: %s", job.id, exc)