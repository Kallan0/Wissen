"""Deterministic conversion from the grounded drafting shape to JSON Resume."""

from __future__ import annotations

import re
from typing import Any

from content_quality import normalize_resume_content


_ISO_DATE = re.compile(r"^[12]\d{3}(?:-(?:0[1-9]|1[0-2])(?:-(?:0[1-9]|[12]\d|3[01]))?)?$")


def _text(value: Any) -> str:
    return str(value or "").strip()


def _url(value: Any) -> str:
    url = _text(value)
    if url and not re.match(r"^[a-z][a-z0-9+.-]*://", url, re.IGNORECASE):
        return f"https://{url}"
    return url


def _date_range(value: Any) -> tuple[str, str]:
    """Return only schema-safe ISO dates; preserve display text in custom data."""
    raw = _text(value)
    if not raw:
        return "", ""
    parts = re.split(r"\s+(?:-|–|—|to)\s+", raw, maxsplit=1, flags=re.IGNORECASE)
    if len(parts) == 1:
        return (parts[0], "") if _ISO_DATE.fullmatch(parts[0]) else ("", "")
    start = parts[0] if _ISO_DATE.fullmatch(parts[0]) else ""
    end = parts[1] if _ISO_DATE.fullmatch(parts[1]) else ""
    return start, end


def _compact(data: dict[str, Any]) -> dict[str, Any]:
    """Remove empty optional values while retaining booleans and numeric zero."""
    result: dict[str, Any] = {}
    for key, value in data.items():
        if isinstance(value, dict):
            value = _compact(value)
        elif isinstance(value, list):
            value = [item for item in value if item not in (None, "", {}, [])]
        if value not in (None, "", {}, []):
            result[key] = value
    return result


def to_json_resume(draft: dict[str, Any]) -> dict[str, Any]:
    """Map a verified internal draft to the official JSON Resume field names."""
    draft = normalize_resume_content(draft)
    contact = draft.get("contact") if isinstance(draft.get("contact"), dict) else {}
    profiles = []
    for network, field in (("LinkedIn", "linkedin"), ("GitHub", "github")):
        url = _url(contact.get(field))
        if url:
            profiles.append({"network": network, "username": "", "url": url})

    basics = _compact({
        "name": _text(draft.get("name")),
        "label": _text(draft.get("title")),
        "email": _text(contact.get("email")),
        "phone": _text(contact.get("phone")),
        "url": _url(contact.get("portfolio")),
        "summary": _text(draft.get("summary")),
        "location": {"address": _text(contact.get("location"))},
        "profiles": profiles,
    })

    work = []
    for item in draft.get("experience", []) if isinstance(draft.get("experience"), list) else []:
        if not isinstance(item, dict):
            continue
        display_date = _text(item.get("duration"))
        start_date, end_date = _date_range(display_date)
        work.append(_compact({
            "name": _text(item.get("company")),
            "position": _text(item.get("role")),
            "location": _text(item.get("location")),
            "startDate": start_date,
            "endDate": end_date,
            "highlights": [_text(value) for value in item.get("bullets", []) if _text(value)],
            "keywords": [_text(value) for value in item.get("technologies", []) if _text(value)],
            "custom": {"wissenPress": {"displayDate": display_date}},
        }))

    projects = []
    for item in draft.get("projects", []) if isinstance(draft.get("projects"), list) else []:
        if not isinstance(item, dict):
            continue
        display_date = _text(item.get("year"))
        start_date, end_date = _date_range(display_date)
        projects.append(_compact({
            "name": _text(item.get("name")),
            "summary": _text(item.get("description")),
            "highlights": [_text(value) for value in (item.get("bullets") or item.get("highlights") or []) if _text(value)],
            "keywords": [_text(value) for value in item.get("technologies", []) if _text(value)],
            "startDate": start_date,
            "endDate": end_date,
            "url": _url(item.get("link")),
            "type": "project",
            "custom": {"wissenPress": {"displayDate": display_date}},
        }))

    education = []
    for item in draft.get("education", []) if isinstance(draft.get("education"), list) else []:
        if not isinstance(item, dict):
            continue
        display_date = _text(item.get("year"))
        start_date, end_date = _date_range(display_date)
        education.append(_compact({
            "institution": _text(item.get("institution")),
            "studyType": _text(item.get("degree")),
            "startDate": start_date,
            "endDate": end_date,
            "score": _text(item.get("details")),
            "custom": {"wissenPress": {
                "displayDate": display_date,
                "location": _text(item.get("location")),
            }},
        }))

    skills = []
    for item in draft.get("skills", []) if isinstance(draft.get("skills"), list) else []:
        if not isinstance(item, dict):
            continue
        keywords = [_text(value) for value in item.get("items", []) if _text(value)]
        if keywords:
            skills.append({"name": _text(item.get("category")) or "Skills", "keywords": keywords})

    return _compact({
        "basics": basics,
        "work": work,
        "education": education,
        "skills": skills,
        "projects": projects,
        "meta": {"version": "v1.0.0"},
        "custom": {"wissenPress": {
            "tailoredMatchNotes": draft.get("tailored_match_notes") or [],
            "aiProvider": _text(draft.get("_ai_provider")),
            "groundingValidation": draft.get("_grounding_validation") or {},
        }},
    })
