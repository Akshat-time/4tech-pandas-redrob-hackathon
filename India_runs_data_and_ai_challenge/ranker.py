#!/usr/bin/env python3
"""Heuristic ranker for the Redrob hackathon.

Reads candidates from JSONL or JSONL.GZ, scores fit against the Senior AI
Engineer JD, and writes the top 100 rows in the submission CSV format.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import json
import math
from datetime import date, datetime
from pathlib import Path
from typing import Iterable


TARGET_ROLE_KEYWORDS = {
    "ai engineer",
    "ml engineer",
    "machine learning engineer",
    "senior ai engineer",
    "search engineer",
    "ranking",
    "retrieval",
    "recommendation",
    "nlp",
    "llm",
    "embeddings",
    "vector search",
    "information retrieval",
    "data scientist",
}

PRODUCTION_EVIDENCE = {
    "production",
    "deployed",
    "shipped",
    "users",
    "scale",
    "ranking",
    "retrieval",
    "search",
    "recommendation",
    "embeddings",
    "vector",
    "evaluation",
    "a/b",
    "ab test",
    "offline",
    "online",
    "fine-tuning",
    "llm",
    "nlp",
    "mlops",
}

CONSULTING_COMPANIES = {
    "tcs",
    "infosys",
    "wipro",
    "accenture",
    "cognizant",
    "capgemini",
    "deloitte",
    "hcl",
    "tech mahindra",
    "mindtree",
    "ltimindtree",
    "l&t infotech",
    "pwc",
    "ey",
    "kpmg",
}

PRODUCT_COMPANY_HINTS = {
    "product",
    "startup",
    "platform",
    "marketplace",
    "saas",
    "consumer",
    "internet",
    "ecommerce",
    "fintech",
    "healthtech",
    "edtech",
    "ai-native",
}

ROLE_EXPERIENCE_KEYWORDS = {
    "embedding": 1.8,
    "embeddings": 1.8,
    "retrieval": 2.0,
    "search": 1.7,
    "ranking": 2.1,
    "recommendation": 1.6,
    "llm": 1.3,
    "fine-tuning": 1.2,
    "finetuning": 1.2,
    "vector": 1.4,
    "milvus": 1.6,
    "faiss": 1.5,
    "qdrant": 1.5,
    "weaviate": 1.5,
    "pinecone": 1.5,
    "opensearch": 1.3,
    "elasticsearch": 1.3,
    "bm25": 1.3,
    "ndcg": 1.9,
    "mrr": 1.8,
    "map": 1.5,
    "ab test": 1.4,
    "a/b": 1.4,
    "offline": 1.0,
    "online": 1.0,
    "python": 1.0,
}

LOCATION_HINTS = {
    "noida",
    "pune",
    "mumbai",
    "delhi",
    "delhi ncr",
    "gurgaon",
    "gurugram",
    "hyderabad",
    "bangalore",
    "bengaluru",
}

HIGH_ENGAGEMENT_SKILLS = {
    "nlp",
    "machine learning",
    "deep learning",
    "llm",
    "embeddings",
    "retrieval",
    "search",
    "recommendation systems",
    "vector databases",
    "milvus",
    "faiss",
    "qdrant",
    "weaviate",
    "pinecone",
    "elasticsearch",
    "opensearch",
    "ranking",
    "fine-tuning llms",
    "lora",
    "qlora",
    "peft",
    "xgboost",
}


def load_candidates(path: Path) -> Iterable[dict]:
    if path.suffix.lower() == ".gz":
        opener = gzip.open
        mode = "rt"
    else:
        opener = open
        mode = "r"

    with opener(path, mode, encoding="utf-8") as handle:
        first_non_empty = None
        for line in handle:
            if line.strip():
                first_non_empty = line.lstrip()
                break

        if first_non_empty is None:
            return

        if first_non_empty.startswith("["):
            handle.seek(0)
            payload = json.load(handle)
            for candidate in payload:
                yield candidate
            return

        yield json.loads(first_non_empty)
        for line in handle:
            if line.strip():
                yield json.loads(line)


def flatten_text(candidate: dict) -> str:
    profile = candidate.get("profile", {})
    skills = candidate.get("skills", [])
    history = candidate.get("career_history", [])

    parts = [
        candidate.get("candidate_id", ""),
        profile.get("anonymized_name", ""),
        profile.get("headline", ""),
        profile.get("summary", ""),
        profile.get("current_title", ""),
        profile.get("current_company", ""),
        profile.get("current_industry", ""),
        profile.get("location", ""),
        profile.get("country", ""),
        " ".join(skill.get("name", "") for skill in skills),
        " ".join(entry.get("title", "") for entry in history),
        " ".join(entry.get("company", "") for entry in history),
        " ".join(entry.get("description", "") for entry in history),
    ]
    return " ".join(parts).lower()


def clamp(value: float, minimum: float = 0.0, maximum: float = 1.0) -> float:
    return max(minimum, min(maximum, value))


def count_keywords(text: str, keywords: Iterable[str]) -> int:
    return sum(1 for keyword in keywords if keyword in text)


def months_since(datestr: str, today: date | None = None) -> int:
    if not datestr:
        return 999
    today = today or date.today()
    parsed = datetime.strptime(datestr, "%Y-%m-%d").date()
    return max(0, (today.year - parsed.year) * 12 + today.month - parsed.month)


def score_candidate(candidate: dict) -> tuple[float, str]:
    profile = candidate.get("profile", {})
    signals = candidate.get("redrob_signals", {})
    history = candidate.get("career_history", [])
    skills = candidate.get("skills", [])

    text = flatten_text(candidate)
    title_text = " ".join(
        [
            profile.get("headline", ""),
            profile.get("current_title", ""),
            profile.get("summary", ""),
            " ".join(entry.get("title", "") for entry in history),
        ]
    ).lower()

    years = float(profile.get("years_of_experience") or 0.0)
    experience_score = math.exp(-((years - 7.0) / 2.3) ** 2)
    if 5.0 <= years <= 9.0:
        experience_score += 0.15
    experience_score = clamp(experience_score)

    role_hits = count_keywords(title_text, TARGET_ROLE_KEYWORDS)
    evidence_hits = count_keywords(text, PRODUCTION_EVIDENCE)
    product_hits = count_keywords(text, PRODUCT_COMPANY_HINTS)
    role_experience = sum(weight for keyword, weight in ROLE_EXPERIENCE_KEYWORDS.items() if keyword in text)
    skill_hits = sum(1 for skill in skills if skill.get("name", "").strip().lower() in HIGH_ENGAGEMENT_SKILLS)

    consulting_only = bool(history) and all(
        any(company_hint in (entry.get("company", "").lower()) for company_hint in CONSULTING_COMPANIES)
        for entry in history
    )
    consulting_penalty = 0.22 if consulting_only else 0.0

    non_product_title = not any(
        keyword in title_text for keyword in ["engineer", "scientist", "ml", "ai", "search", "ranking", "data", "research"]
    )
    keyword_stuffer_penalty = 0.0
    if skill_hits >= 6 and non_product_title and role_experience < 2.0:
        keyword_stuffer_penalty = 0.28

    location_text = f"{profile.get('location', '')} {profile.get('country', '')}"
    location_hits = count_keywords(location_text.lower(), LOCATION_HINTS)
    location_score = 0.15 if location_hits else 0.0
    if str(profile.get("country", "")).lower() == "india":
        location_score += 0.12
    if signals.get("willing_to_relocate"):
        location_score += 0.07
    preferred_mode = str(signals.get("preferred_work_mode", "")).lower()
    if preferred_mode in {"hybrid", "flexible", "onsite"}:
        location_score += 0.05

    behavior_score = 0.0
    if signals.get("open_to_work_flag"):
        behavior_score += 0.10
    behavior_score += clamp(float(signals.get("recruiter_response_rate") or 0.0), 0.0, 1.0) * 0.22
    behavior_score += clamp(1.0 - float(signals.get("avg_response_time_hours") or 0.0) / 168.0, 0.0, 1.0) * 0.08
    behavior_score += clamp(float(signals.get("interview_completion_rate") or 0.0), 0.0, 1.0) * 0.08
    offer_acceptance = float(signals.get("offer_acceptance_rate") or -1.0)
    if offer_acceptance >= 0:
        behavior_score += offer_acceptance * 0.04
    behavior_score += clamp(float(signals.get("profile_completeness_score") or 0.0) / 100.0, 0.0, 1.0) * 0.05
    github_score = float(signals.get("github_activity_score") or -1.0)
    if github_score >= 0:
        behavior_score += clamp(github_score / 100.0, 0.0, 1.0) * 0.04
    behavior_score += clamp(math.log1p(float(signals.get("saved_by_recruiters_30d") or 0.0)) / 2.0, 0.0, 1.0) * 0.03
    behavior_score += clamp(math.log1p(float(signals.get("search_appearance_30d") or 0.0)) / 6.0, 0.0, 1.0) * 0.02
    behavior_score += 0.03 if signals.get("verified_email") else 0.0
    behavior_score += 0.03 if signals.get("verified_phone") else 0.0
    behavior_score += 0.02 if signals.get("linkedin_connected") else 0.0
    behavior_score = clamp(behavior_score)

    recency_score = 0.0
    last_active = signals.get("last_active_date")
    if last_active:
        months = months_since(last_active)
        recency_score = clamp(1.0 - months / 18.0, 0.0, 1.0) * 0.15

    endorse = clamp(float(signals.get("endorsements_received") or 0.0) / 80.0, 0.0, 1.0) * 0.05
    connections = clamp(float(signals.get("connection_count") or 0.0) / 500.0, 0.0, 1.0) * 0.03

    raw_score = (
        0.22 * experience_score
        + 0.18 * clamp(role_hits / 4.0, 0.0, 1.0)
        + 0.18 * clamp((role_experience + evidence_hits + 0.75 * product_hits) / 12.0, 0.0, 1.0)
        + 0.12 * clamp(skill_hits / 5.0, 0.0, 1.0)
        + location_score
        + behavior_score
        + recency_score
        + endorse
        + connections
        + 0.08 * clamp((profile.get("years_of_experience") or 0.0) / 15.0, 0.0, 1.0)
    )

    raw_score -= consulting_penalty
    raw_score -= keyword_stuffer_penalty

    raw_score = clamp(raw_score, 0.0, 1.0)

    top_reasons = []
    current_title = profile.get("current_title") or profile.get("headline") or "candidate"
    if role_experience >= 2.0:
        top_reasons.append("production ML/search experience")
    if skill_hits >= 3:
        top_reasons.append(f"{skill_hits} relevant AI skills")
    if behavior_score >= 0.35:
        top_reasons.append("strong engagement signals")
    if location_hits or signals.get("willing_to_relocate"):
        top_reasons.append("location-compatible")
    if consulting_only and raw_score < 0.6:
        top_reasons.append("consulting-only career path")
    if not top_reasons:
        top_reasons.append("general fit")

    summary = f"{current_title}; " + "; ".join(top_reasons[:3]) + "."
    if len(summary) > 220:
        summary = summary[:217].rstrip() + "..."

    return raw_score, summary


def write_submission(rows: list[tuple[str, float, str]], output_path: Path) -> None:
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["candidate_id", "rank", "score", "reasoning"])
        for rank, (candidate_id, score, reasoning) in enumerate(rows, start=1):
            writer.writerow([candidate_id, rank, f"{score:.4f}", reasoning])


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a Redrob submission CSV.")
    parser.add_argument(
        "input_path",
        nargs="?",
        default="candidates.jsonl",
        help="Path to candidates.jsonl or candidates.jsonl.gz",
    )
    parser.add_argument(
        "--output",
        default="submission.csv",
        help="Output CSV path",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=100,
        help="Number of candidates to write",
    )
    args = parser.parse_args()

    input_path = Path(args.input_path)
    if not input_path.exists():
        raise SystemExit(f"Input file not found: {input_path}")

    scored: list[tuple[str, float, str]] = []
    for candidate in load_candidates(input_path):
        candidate_id = candidate.get("candidate_id")
        if not candidate_id:
            continue
        score, reasoning = score_candidate(candidate)
        scored.append((candidate_id, score, reasoning))

    scored.sort(key=lambda item: (-item[1], item[0]))
    output_rows = scored[: args.top_k]

    output_path = Path(args.output)
    write_submission(output_rows, output_path)
    print(f"Wrote {len(output_rows)} rows to {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())