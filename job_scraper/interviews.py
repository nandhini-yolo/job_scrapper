from __future__ import annotations

from dataclasses import dataclass

from .models import Job


@dataclass(frozen=True)
class InterviewProfile:
    difficulty: int
    label: str
    stages: str
    skills: str
    basis: str


DEFAULT_PROFILE = InterviewProfile(
    difficulty=3,
    label="Moderate",
    stages="Recruiter screen; coding; role-specific technical interview; behavioral",
    skills="Python, SQL, data structures, system design, pipelines",
    basis="Estimate based on role scope; verify with current candidate reports",
)

COMPANY_PROFILES = {
    "DRW": InterviewProfile(4, "Moderate-hard", "Recruiter; coding; systems/data design; team interviews", "Python, C++/systems, market data, distributed systems, trading domain", "Quant trading firm pattern; role-specific estimate"),
    "Adyen": InterviewProfile(3, "Moderate", "Recruiter; technical screen; coding; system design; team/values", "Python, SQL, data modeling, distributed systems, cloud", "Fintech engineering pattern; role-specific estimate"),
    "Spotify": InterviewProfile(3, "Moderate", "Recruiter; coding; technical design; collaboration/leadership", "Python, SQL, data platform, APIs, distributed systems", "Large product-company pattern; role-specific estimate"),
    "Databricks": InterviewProfile(4, "Hard", "Recruiter; coding; system design; domain deep dive; behavioral", "Python/Scala, Spark, SQL, distributed systems, lakehouse", "Data-platform company pattern; role-specific estimate"),
    "Catawiki": InterviewProfile(2, "Relatively easier", "Recruiter; technical screen; practical coding; team fit", "Python, SQL, ML/data pipelines, cloud, experimentation", "Scale-up pattern; role-specific estimate"),
    "IMC Trading": InterviewProfile(5, "Very hard", "Recruiter; coding/problem solving; systems/domain rounds; behavioral", "Algorithms, Python/C++, low latency, distributed systems, trading", "Quant trading firm pattern; role-specific estimate"),
    "Flow Traders": InterviewProfile(4, "Moderate-hard", "Recruiter; coding; technical/domain; team interviews", "Python/C++, market data, distributed systems, trading", "Quant trading firm pattern; role-specific estimate"),
    "Jane Street": InterviewProfile(5, "Very hard", "Recruiter; probability/problem solving; coding; technical rounds", "Algorithms, probability, Python/OCaml/C++, systems", "Quant trading firm pattern; role-specific estimate"),
    "Palantir": InterviewProfile(4, "Hard", "Recruiter; coding; system design; deployment/team fit", "Python, algorithms, distributed systems, APIs, data modeling", "Product engineering pattern; role-specific estimate"),
    "Elastic": InterviewProfile(3, "Moderate", "Recruiter; coding or practical exercise; systems; behavioral", "Python, distributed systems, observability, cloud, APIs", "Distributed-product pattern; role-specific estimate"),
}


def interview_profile(job: Job) -> InterviewProfile:
    return COMPANY_PROFILES.get(job.company, DEFAULT_PROFILE)