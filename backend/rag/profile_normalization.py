from typing import Any, Dict, List


def _text(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""


def _string_list(value: Any) -> List[str]:
    if isinstance(value, str):
        candidates = value.split(",")
    elif isinstance(value, list):
        candidates = value
    else:
        candidates = []
    return [item.strip() for item in candidates if isinstance(item, str) and item.strip()]


def normalize_profile_submission(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Validate a raw questionnaire payload and produce the ingestion schema.

    No identity, role, organization, or skill fallback is allowed at this
    boundary. Missing optional sections are omitted; incomplete factual records
    are rejected so placeholder text cannot enter the knowledge base.
    """
    name = _text(payload.get("name"))
    if not name:
        raise ValueError("Full name is required.")

    contact_input = payload.get("contact") if isinstance(payload.get("contact"), dict) else {}
    contact = {
        field: _text(contact_input.get(field))
        for field in ("email", "phone", "location", "linkedin", "github", "portfolio")
    }

    skills_input = payload.get("skills_text", payload.get("skills", []))
    if isinstance(skills_input, list) and all(isinstance(group, dict) for group in skills_input):
        skills = [
            {"category": _text(group.get("category")) or "Core Technical Competencies", "items": _string_list(group.get("items"))}
            for group in skills_input
            if _string_list(group.get("items"))
        ]
    else:
        skill_items = _string_list(skills_input)
        skills = [{"category": "Core Technical Competencies", "items": skill_items}] if skill_items else []

    experiences = []
    for item in payload.get("experience", []) if isinstance(payload.get("experience"), list) else []:
        if not isinstance(item, dict):
            continue
        company, role = _text(item.get("company")), _text(item.get("role"))
        has_content = any((company, role, _text(item.get("duration")), _text(item.get("location")), *_string_list(item.get("bullets"))))
        if not has_content:
            continue
        if not company or not role:
            raise ValueError("Each experience must include both company and role.")
        experiences.append({
            "company": company,
            "role": role,
            "duration": _text(item.get("duration")),
            "location": _text(item.get("location")),
            "bullets": _string_list(item.get("bullets")),
            "technologies": _string_list(item.get("technologies")),
        })

    projects = []
    for item in payload.get("projects", []) if isinstance(payload.get("projects"), list) else []:
        if not isinstance(item, dict):
            continue
        name_value = _text(item.get("name"))
        technologies = _string_list(item.get("technologies_text", item.get("technologies", [])))
        highlights = _string_list(item.get("highlights", item.get("bullets", [])))
        has_content = any((name_value, _text(item.get("description")), _text(item.get("link")), *technologies, *highlights))
        if not has_content:
            continue
        if not name_value:
            raise ValueError("Each project must include a name.")
        projects.append({
            "name": name_value,
            "description": _text(item.get("description")),
            "technologies": technologies,
            "highlights": highlights,
            "link": _text(item.get("link")),
        })

    education = []
    for item in payload.get("education", []) if isinstance(payload.get("education"), list) else []:
        if not isinstance(item, dict):
            continue
        institution, degree = _text(item.get("institution")), _text(item.get("degree"))
        has_content = any((institution, degree, _text(item.get("year")), _text(item.get("details"))))
        if not has_content:
            continue
        if not institution or not degree:
            raise ValueError("Each education record must include both institution and degree.")
        education.append({
            "institution": institution,
            "degree": degree,
            "year": _text(item.get("year")),
            "details": _text(item.get("details")),
        })

    return {
        "name": name,
        "title": _text(payload.get("title")),
        "contact": contact,
        "summary": _text(payload.get("summary")),
        "skills": skills,
        "experience": experiences,
        "projects": projects,
        "education": education,
    }
