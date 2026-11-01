"""Deterministic content cleanup for ingestion and resume rendering."""

from copy import deepcopy
from difflib import SequenceMatcher
import re
from typing import Any, Dict, Iterable, List


_BULLET_PREFIX = re.compile(r"^\s*(?:[-*\u2022\u25aa\u25e6]+|\d+[.)])\s*")
_SPACE = re.compile(r"\s+")
_KEY_CHARS = re.compile(r"[^a-z0-9]+")


def clean_text(value: Any) -> str:
    """Return a single-line, whitespace-normalized string."""
    if not isinstance(value, str):
        return ""
    return _SPACE.sub(" ", value).strip()


def content_key(value: Any) -> str:
    """Canonical key used for case/punctuation-insensitive duplicate checks."""
    return _KEY_CHARS.sub(" ", clean_text(value).lower()).strip()


def concise_bullet(value: Any, max_words: int = 30, max_chars: int = 220) -> str:
    """Normalize a bullet and cap it at a readable resume length."""
    text = clean_text(_BULLET_PREFIX.sub("", value if isinstance(value, str) else ""))
    if not text:
        return ""
    words = text.split()
    truncated = len(words) > max_words or len(text) > max_chars
    text = " ".join(words[:max_words])
    if len(text) > max_chars:
        text = text[:max_chars].rsplit(" ", 1)[0]
    if truncated:
        text = text.rstrip(".,;: -") + "\u2026"
    return text


def unique_texts(
    values: Iterable[Any],
    *,
    limit: int | None = None,
    concise: bool = False,
    near_duplicate_threshold: float = 0.92,
) -> List[str]:
    """Keep ordered, meaningful strings while removing exact and near duplicates."""
    result: List[str] = []
    keys: List[str] = []
    for value in values:
        text = concise_bullet(value) if concise else clean_text(value)
        key = content_key(text)
        if not key:
            continue
        if any(
            key == existing
            or SequenceMatcher(None, key, existing).ratio() >= near_duplicate_threshold
            for existing in keys
        ):
            continue
        result.append(text)
        keys.append(key)
        if limit is not None and len(result) >= limit:
            break
    return result


def _list(value: Any) -> List[Any]:
    return value if isinstance(value, list) else []


def _merge_records(records: Iterable[Any], section: str) -> List[Dict[str, Any]]:
    merged: Dict[str, Dict[str, Any]] = {}
    order: List[str] = []
    for raw in records:
        if not isinstance(raw, dict):
            continue
        item = deepcopy(raw)
        if section == "experience":
            identity = "|".join(content_key(item.get(field)) for field in ("company", "role", "duration"))
            bullet_values = _list(item.get("bullets")) + _list(item.get("highlights"))
        elif section == "projects":
            identity = content_key(item.get("name")) or content_key(item.get("link"))
            # Project detail belongs in bullets in the exported resume.
            bullet_values = [item.get("description")] + _list(item.get("bullets")) + _list(item.get("highlights"))
        else:
            identity = "|".join(content_key(item.get(field)) for field in ("institution", "degree", "year"))
            bullet_values = []

        identity = identity or content_key(str(sorted(item.items())))
        if identity not in merged:
            merged[identity] = item
            merged[identity]["_bullet_values"] = []
            order.append(identity)
        current = merged[identity]
        current["_bullet_values"].extend(bullet_values)
        if section in {"experience", "projects"}:
            current["technologies"] = unique_texts(
                _list(current.get("technologies")) + _list(item.get("technologies")),
                near_duplicate_threshold=1.0,
            )
        for field, value in item.items():
            if not current.get(field) and value:
                current[field] = value

    result: List[Dict[str, Any]] = []
    for identity in order:
        item = merged[identity]
        bullet_values = item.pop("_bullet_values")
        if section == "experience":
            item["bullets"] = unique_texts(bullet_values, concise=True, limit=4)
        elif section == "projects":
            item["description"] = ""
            item["bullets"] = unique_texts(bullet_values, concise=True, limit=3)
            item["highlights"] = list(item["bullets"])
        result.append(item)
    return result


def normalize_resume_content(data: Dict[str, Any]) -> Dict[str, Any]:
    """Consolidate duplicate resume entities and enforce concise PDF bullets."""
    cleaned = deepcopy(data)
    cleaned["experience"] = _merge_records(_list(data.get("experience")), "experience")
    cleaned["projects"] = _merge_records(_list(data.get("projects")), "projects")
    cleaned["education"] = _merge_records(_list(data.get("education")), "education")

    # Do not print the same achievement under multiple entries or sections.
    seen_bullets: set[str] = set()
    for section, limit in (("experience", 3), ("projects", 3)):
        for item in cleaned[section]:
            unique: List[str] = []
            for bullet in item.get("bullets", []):
                key = content_key(bullet)
                if key and key not in seen_bullets:
                    seen_bullets.add(key)
                    unique.append(bullet)
                if len(unique) >= limit:
                    break
            item["bullets"] = unique
            if section == "projects":
                item["highlights"] = list(unique)
    return cleaned
