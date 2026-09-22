"""Generate grounded resume-tailoring SFT examples with a local Ollama model.

The generator has no sample-persona fallback. It refuses to write data unless
ChromaDB contains a real candidate name and verified work experience. Outputs
span three role families while every prompt is restricted to actual profile data.

Example:
    python backend/finetuning/dataset_generator.py --count 150 \
        --output backend/data/finetuning/generated_dataset.jsonl
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

import httpx

CURRENT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = CURRENT_DIR.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from ai.generator import extract_json  # noqa: E402
from ai.prompts import STRICT_SYSTEM_PROMPT  # noqa: E402
from config import settings  # noqa: E402
from rag.vectorstore import vector_store  # noqa: E402

REQUIRED_RESUME_KEYS = {
    "name", "title", "contact", "summary", "skills",
    "experience", "projects", "education",
}


@dataclass(frozen=True)
class RoleFamily:
    title: str
    skill_terms: tuple[str, ...]
    responsibilities: tuple[str, ...]
    emphases: tuple[str, ...]


ROLE_FAMILIES = (
    RoleFamily(
        title="Python Backend Developer",
        skill_terms=("python", "fastapi", "django", "flask", "sql", "postgresql", "api", "docker", "redis"),
        responsibilities=(
            "Build reliable Python services and well-designed APIs.",
            "Improve data access, observability, testing, and deployment workflows.",
            "Collaborate on secure, maintainable backend architecture.",
        ),
        emphases=(
            "API reliability and maintainable service design",
            "data processing and database-backed applications",
            "testing, automation, and production operations",
            "performance and asynchronous workflows",
        ),
    ),
    RoleFamily(
        title="React / Next.js Frontend Developer",
        skill_terms=("react", "next.js", "nextjs", "javascript", "typescript", "css", "tailwind", "frontend", "web"),
        responsibilities=(
            "Build responsive, accessible React and Next.js interfaces.",
            "Translate product requirements into reusable frontend components.",
            "Improve browser performance, usability, and frontend quality.",
        ),
        emphases=(
            "responsive UI engineering and component reuse",
            "accessibility and interaction quality",
            "frontend performance and maintainability",
            "design-to-code collaboration",
        ),
    ),
    RoleFamily(
        title="Figma UI/UX Designer",
        skill_terms=("figma", "ui", "ux", "design", "prototype", "wireframe", "canva", "accessibility", "user research"),
        responsibilities=(
            "Create user flows, wireframes, prototypes, and polished interface designs.",
            "Apply reusable design systems and accessible interaction patterns.",
            "Collaborate with engineering to ship faithful, usable experiences.",
        ),
        emphases=(
            "design systems and reusable component libraries",
            "interaction design and prototyping",
            "user-centered problem solving and accessibility",
            "developer handoff and design implementation",
        ),
    ),
)

INDUSTRIES = (
    "developer tools", "financial technology", "health technology",
    "education technology", "e-commerce", "business productivity",
    "creative software", "data platforms", "consumer applications", "enterprise SaaS",
)


def _flatten_skills(profile: dict[str, Any]) -> list[str]:
    skills: list[str] = []
    for group in profile.get("skills") or []:
        for item in group.get("items") or []:
            value = str(item).strip()
            if value and value.casefold() not in {known.casefold() for known in skills}:
                skills.append(value)
    for section in ("experiences", "projects"):
        for record in profile.get(section) or []:
            for item in record.get("technologies") or []:
                value = str(item).strip()
                if value and value.casefold() not in {known.casefold() for known in skills}:
                    skills.append(value)
    return skills


def _deduplicate_experiences(experiences: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], dict[str, Any]] = {}
    for experience in experiences:
        key = (
            str(experience.get("company") or "").strip().casefold(),
            str(experience.get("role") or "").strip().casefold(),
        )
        if key not in grouped:
            grouped[key] = {
                "company": experience.get("company") or "",
                "role": experience.get("role") or "",
                "duration": experience.get("duration") or "",
                "location": experience.get("location") or "",
                "technologies": [],
                "evidence": [],
            }
        target = grouped[key]
        for technology in experience.get("technologies") or []:
            if technology and technology not in target["technologies"]:
                target["technologies"].append(technology)
        content = str(experience.get("content") or "").strip()
        if content and content not in target["evidence"]:
            target["evidence"].append(content)
    return list(grouped.values())


def _deduplicate_projects(projects: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, dict[str, Any]] = {}
    for project in projects:
        name = str(project.get("name") or "").strip()
        if not name:
            continue
        key = name.casefold()
        if key not in grouped:
            grouped[key] = {
                "name": name,
                "description": "",
                "technologies": [],
                "link": project.get("link") or "",
            }
        target = grouped[key]
        description = str(project.get("description") or "").strip()
        if len(description) > len(target["description"]):
            target["description"] = description
        for technology in project.get("technologies") or []:
            if technology and technology not in target["technologies"]:
                target["technologies"].append(technology)
        if not target["link"] and project.get("link"):
            target["link"] = project["link"]
    return list(grouped.values())


def load_candidate_profile() -> dict[str, Any]:
    """Return verified profile data or fail before an output file is touched."""
    profile = vector_store.get_candidate_profile()
    if not profile or not profile.get("exists"):
        raise ValueError("Export refused: Verified candidate profile is missing from the knowledge base.")
    candidate = profile.get("candidate") or {}
    if not str(candidate.get("name") or "").strip():
        raise ValueError("Export refused: Verified candidate name is missing from the profile.")
    if not profile.get("experiences") or len(profile["experiences"]) == 0:
        raise ValueError("Export refused: Verified experience is missing from the profile.")
    profile["experiences"] = _deduplicate_experiences(profile["experiences"])
    profile["projects"] = _deduplicate_projects(profile.get("projects") or [])
    profile["skills_flat"] = _flatten_skills(profile)
    if not profile["skills_flat"]:
        raise ValueError("Export refused: Verified skills are missing from the profile.")
    return profile


def _role_relevant_skills(profile_skills: list[str], role: RoleFamily) -> list[str]:
    return [
        skill for skill in profile_skills
        if any(term in skill.casefold() or skill.casefold() in term for term in role.skill_terms)
    ]


def _project_relevance(project: dict[str, Any], role: RoleFamily) -> int:
    haystack = " ".join(
        [
            str(project.get("name") or ""),
            str(project.get("description") or ""),
            " ".join(str(item) for item in project.get("technologies") or []),
        ]
    ).casefold()
    return sum(1 for term in role.skill_terms if term in haystack)


def _profile_context(profile: dict[str, Any], role: RoleFamily) -> str:
    ranked_projects = sorted(
        profile.get("projects") or [],
        key=lambda project: _project_relevance(project, role),
        reverse=True,
    )
    context = {
        "candidate": profile.get("candidate") or {},
        "experience": profile.get("experiences") or [],
        "projects": ranked_projects[:3],
        "skills": profile.get("skills") or [],
        "education": profile.get("education") or [],
    }
    return json.dumps(context, ensure_ascii=False, indent=2)


def _build_job_description(role: RoleFamily, variation_index: int, rng: random.Random) -> str:
    industry = INDUSTRIES[variation_index % len(INDUSTRIES)]
    emphasis = role.emphases[(variation_index // len(INDUSTRIES)) % len(role.emphases)]
    responsibilities = list(role.responsibilities)
    rng.shuffle(responsibilities)
    return (
        f"Target role: {role.title}\nIndustry: {industry}\nPrimary emphasis: {emphasis}\n"
        "Responsibilities:\n- " + "\n- ".join(responsibilities)
        + "\nThe employer values concise evidence, truthful impact statements, and clear collaboration."
    )


def _build_user_prompt(
    profile: dict[str, Any], role: RoleFamily, job_description: str, variation_index: int
) -> str:
    relevant = _role_relevant_skills(profile["skills_flat"], role)
    relevant_text = ", ".join(relevant) if relevant else "No directly matching verified skills detected"
    candidate_name = str((profile.get("candidate") or {}).get("name") or "").strip()
    return f"""Create one tailored resume for the job scenario below.

VARIATION ID: {role.title}-{variation_index:03d}
TARGET JOB:
{job_description}

VERIFIED SKILLS RELEVANT TO THIS ROLE:
{relevant_text}

VERIFIED CANDIDATE PROFILE:
{_profile_context(profile, role)}

Rules:
1. Use only facts explicitly present in VERIFIED CANDIDATE PROFILE.
2. Never invent technologies, employers, dates, education, metrics, seniority, or design methods.
3. If this role is partially supported, position adjacent transferable evidence honestly; do not fill gaps.
4. CRITICAL: The candidate's name is exactly '{candidate_name}'. Do not alter, abbreviate, or omit this name under any circumstances.
5. Do not output the name, contact details, company names, dates, skill lists, education, or project metadata; Python injects those deterministic fields.
6. Vary sentence openings and structure from other examples while remaining concise.
7. Return JSON only with this compact shape:
   {{"summary":"...","experience_bullets":[{{"index":0,"bullets":["..."]}}],"project_bullets":[{{"index":0,"bullets":["..."]}}],"tailored_match_notes":["..."]}}
8. Indices refer to the zero-based order of experience and projects in VERIFIED CANDIDATE PROFILE.
9. Arrays may be empty when no verified evidence exists. Produce at most two bullets for each experience and one bullet for each project.
"""


def _inject_verified_name(
    result: Optional[dict[str, Any]], profile: dict[str, Any]
) -> Optional[dict[str, Any]]:
    """Make the deterministic identity field independent of model behavior."""
    if isinstance(result, dict):
        result["name"] = str((profile.get("candidate") or {}).get("name") or "").strip()
    return result


def _indexed_bullets(value: Any, limit: int) -> dict[int, list[str]]:
    mapped: dict[int, list[str]] = {}
    if not isinstance(value, list):
        return mapped
    for item in value:
        if not isinstance(item, dict) or not isinstance(item.get("index"), int):
            continue
        bullets = [
            str(bullet).strip() for bullet in item.get("bullets") or []
            if isinstance(bullet, str) and bullet.strip()
        ]
        mapped[item["index"]] = bullets[:limit]
    return mapped


def _assemble_verified_resume(
    generated: Optional[dict[str, Any]], profile: dict[str, Any], role: RoleFamily
) -> dict[str, Any]:
    """Combine probabilistic prose with deterministic verified profile fields."""
    if not isinstance(generated, dict):
        raise ValueError("Ollama returned no valid JSON object.")
    summary = generated.get("summary")
    if not isinstance(summary, str) or not summary.strip():
        raise ValueError("Ollama output is missing a non-empty summary.")

    experience_bullets = _indexed_bullets(generated.get("experience_bullets"), 2)
    project_bullets = _indexed_bullets(generated.get("project_bullets"), 1)
    experiences: list[dict[str, Any]] = []
    for index, experience in enumerate(profile.get("experiences") or []):
        experiences.append({
            "company": experience.get("company") or "",
            "role": experience.get("role") or "",
            "duration": experience.get("duration") or "",
            "location": experience.get("location") or "",
            "technologies": list(experience.get("technologies") or []),
            "bullets": experience_bullets.get(index, []),
        })

    ranked_projects = sorted(
        profile.get("projects") or [],
        key=lambda project: _project_relevance(project, role),
        reverse=True,
    )[:3]
    projects: list[dict[str, Any]] = []
    for index, project in enumerate(ranked_projects):
        projects.append({
            "name": project.get("name") or "",
            "description": project.get("description") or "",
            "technologies": list(project.get("technologies") or []),
            "bullets": project_bullets.get(index, []),
            "link": project.get("link") or "",
        })

    relevant_skills = _role_relevant_skills(profile["skills_flat"], role)
    notes = [
        str(note).strip() for note in generated.get("tailored_match_notes") or []
        if isinstance(note, str) and note.strip()
    ]
    candidate = dict(profile.get("candidate") or {})
    return {
        "name": str(candidate.pop("name", "")).strip(),
        "title": role.title,
        "contact": candidate,
        "summary": summary.strip(),
        "skills": [{"category": "Verified Role-Relevant Skills", "items": relevant_skills}],
        "experience": experiences,
        "projects": projects,
        "education": list(profile.get("education") or []),
        "tailored_match_notes": notes[:4],
    }


def _validate_generated_resume(result: Optional[dict[str, Any]], profile: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(result, dict):
        raise ValueError("Ollama returned no valid JSON object.")
    missing = sorted(REQUIRED_RESUME_KEYS - result.keys())
    if missing:
        raise ValueError(f"Ollama output is missing required keys: {', '.join(missing)}")
    expected_name = str((profile.get("candidate") or {}).get("name") or "").strip()
    if str(result.get("name") or "").strip().casefold() != expected_name.casefold():
        raise ValueError("Ollama changed the verified candidate name.")
    for key in ("skills", "experience", "projects", "education"):
        if not isinstance(result[key], list):
            raise ValueError(f"Ollama output field '{key}' must be an array.")
    if not isinstance(result["contact"], dict):
        raise ValueError("Ollama output field 'contact' must be an object.")
    return result


def _generate_with_ollama(
    client: httpx.Client,
    model: str,
    profile: dict[str, Any],
    role: RoleFamily,
    job_description: str,
    variation_index: int,
    max_attempts: int = 3,
) -> dict[str, Any]:
    user_prompt = _build_user_prompt(profile, role, job_description, variation_index)
    last_error: Optional[Exception] = None
    for attempt in range(1, max_attempts + 1):
        try:
            response = client.post(
                f"{settings.OLLAMA_BASE_URL.rstrip('/')}/api/generate",
                json={
                    "model": model,
                    "prompt": f"{STRICT_SYSTEM_PROMPT.strip()}\n\n{user_prompt}",
                    "stream": False,
                    "format": "json",
                    "options": {
                        "temperature": 0.25 + (0.05 * ((variation_index + attempt) % 3)),
                        "top_p": 0.9,
                        "seed": 10_000 + variation_index + attempt,
                        "num_predict": 600,
                    },
                },
            )
            response.raise_for_status()
            generated = extract_json(response.json().get("response", ""))
            assembled = _assemble_verified_resume(generated, profile, role)
            assembled = _inject_verified_name(assembled, profile)
            return _validate_generated_resume(assembled, profile)
        except (httpx.HTTPError, ValueError, json.JSONDecodeError) as exc:
            last_error = exc
    raise RuntimeError(
        f"Generation failed for {role.title} variation {variation_index} after {max_attempts} attempts: {last_error}"
    )


def _write_jsonl_atomic(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8", newline="\n") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n")
    temporary.replace(path)


def build_dataset(
    count: int = 150,
    output_path: Optional[str] = None,
    model: Optional[str] = None,
    seed: int = 42,
    workers: int = 3,
) -> str:
    """Generate 100–200 candidate-grounded examples and atomically write JSONL."""
    if not 100 <= count <= 200:
        raise ValueError("Dataset count must be between 100 and 200 examples.")
    if not 1 <= workers <= 4:
        raise ValueError("workers must be between 1 and 4.")
    profile = load_candidate_profile()  # Validate before touching the output.
    output = Path(output_path) if output_path else CURRENT_DIR / "generated_dataset.jsonl"
    selected_model = model or settings.OLLAMA_DEFAULT_MODEL
    rng = random.Random(seed)
    role_counters = {role.title: 0 for role in ROLE_FAMILIES}
    jobs: list[tuple[int, RoleFamily, int, str, str]] = []
    for index in range(count):
        role = ROLE_FAMILIES[index % len(ROLE_FAMILIES)]
        role_index = role_counters[role.title]
        role_counters[role.title] += 1
        job_description = _build_job_description(role, role_index, rng)
        user_prompt = _build_user_prompt(profile, role, job_description, role_index)
        jobs.append((index, role, role_index, job_description, user_prompt))

    records_by_index: dict[int, dict[str, Any]] = {}

    with httpx.Client(timeout=httpx.Timeout(180.0)) as client:
        def generate_job(job: tuple[int, RoleFamily, int, str, str]) -> tuple[int, str, dict[str, Any]]:
            index, role, role_index, job_description, user_prompt = job
            assistant_output = _generate_with_ollama(
                client, selected_model, profile, role, job_description, role_index
            )
            record = {
                "messages": [
                    {"role": "system", "content": STRICT_SYSTEM_PROMPT.strip()},
                    {"role": "user", "content": user_prompt.strip()},
                    {"role": "assistant", "content": json.dumps(assistant_output, ensure_ascii=False, separators=(",", ":"))},
                ]
            }
            return index, role.title, record

        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = [executor.submit(generate_job, job) for job in jobs]
            completed = 0
            for future in as_completed(futures):
                index, role_title, record = future.result()
                records_by_index[index] = record
                completed += 1
                print(f"Generated {completed}/{count}: {role_title}", flush=True)

    records = [records_by_index[index] for index in range(count)]
    _write_jsonl_atomic(output, records)
    print(f"Generated {len(records)} grounded examples -> {output}")
    return str(output)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate grounded Ollama SFT examples.")
    parser.add_argument("--count", type=int, default=150)
    parser.add_argument("--output", default="backend/data/finetuning/generated_dataset.jsonl")
    parser.add_argument("--model", default=os.getenv("OLLAMA_DEFAULT_MODEL", settings.OLLAMA_DEFAULT_MODEL))
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--workers", type=int, default=3)
    args = parser.parse_args()
    try:
        build_dataset(args.count, args.output, args.model, args.seed, args.workers)
    except (ValueError, RuntimeError, httpx.HTTPError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
