"""Audit fine-tuning JSONL files against the verified ChromaDB profile.

This tool is read-only with respect to datasets and the knowledge base. It
writes machine-readable and Markdown reports plus a deterministic manual-review
packet under ``backend/data/finetuning/reports`` by default.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import re
import sys
from collections import Counter
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


CURRENT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = CURRENT_DIR.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from finetuning.dataset_generator import load_candidate_profile  # noqa: E402
from finetuning.finetune_llama3 import (  # noqa: E402
    DatasetValidationError,
    load_validated_records,
)


NUMBER_PATTERN = re.compile(
    r"(?<![A-Za-z])(?:[$€£₹]\s*)?\d+(?:[.,]\d+)*(?:\s?%|\+|[kKmMbB])?(?![A-Za-z])"
)
SPACE_PATTERN = re.compile(r"\s+")
ROLE_FAMILIES = {
    "Python Backend Developer",
    "React / Next.js Frontend Developer",
    "Figma UI/UX Designer",
}
STATIC_EXPERIENCE_FIELDS = ("company", "role", "duration", "location", "technologies")
STATIC_PROJECT_FIELDS = ("name", "description", "technologies", "link")


@dataclass
class AuditFinding:
    severity: str
    code: str
    dataset: str
    record_index: int | None
    field: str
    message: str


@dataclass
class AuditReport:
    created_at: str
    training_path: str
    holdout_path: str
    training_sha256: str
    holdout_sha256: str
    training_records: int
    holdout_records: int
    exact_overlap: int
    unique_candidate_names: int
    role_counts: dict[str, int]
    duplicate_summaries: int
    duplicate_bullets: int
    findings: list[AuditFinding] = field(default_factory=list)

    @property
    def errors(self) -> int:
        return sum(item.severity == "error" for item in self.findings)

    @property
    def warnings(self) -> int:
        return sum(item.severity == "warning" for item in self.findings)

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["errors"] = self.errors
        result["warnings"] = self.warnings
        result["status"] = "fail" if self.errors else "manual_review_required"
        return result


def _digest_bytes(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _digest_record(record: dict[str, Any]) -> str:
    canonical = json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _normalize_text(value: str) -> str:
    return SPACE_PATTERN.sub(" ", value.strip().casefold())


def _assistant_payload(record: dict[str, Any]) -> dict[str, Any]:
    return json.loads(record["messages"][-1]["content"])


def _profile_evidence_text(profile: dict[str, Any]) -> str:
    payload = {
        "candidate": profile.get("candidate") or {},
        "experiences": profile.get("experiences") or [],
        "projects": profile.get("projects") or [],
        "skills": profile.get("skills") or [],
        "education": profile.get("education") or [],
    }
    return json.dumps(payload, ensure_ascii=False).casefold()


def _generated_prose(payload: dict[str, Any]) -> Iterable[tuple[str, str]]:
    summary = payload.get("summary")
    if isinstance(summary, str):
        yield "summary", summary
    for section in ("experience", "projects"):
        for item_index, item in enumerate(payload.get(section) or []):
            if not isinstance(item, dict):
                continue
            for bullet_index, bullet in enumerate(item.get("bullets") or []):
                if isinstance(bullet, str):
                    yield f"{section}[{item_index}].bullets[{bullet_index}]", bullet


def _static_key(item: dict[str, Any], fields: tuple[str, ...]) -> str:
    selected = {field: item.get(field) for field in fields}
    return json.dumps(selected, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _add(
    findings: list[AuditFinding],
    severity: str,
    code: str,
    dataset: str,
    record_index: int | None,
    field: str,
    message: str,
) -> None:
    findings.append(AuditFinding(severity, code, dataset, record_index, field, message))


def _audit_record(
    payload: dict[str, Any],
    *,
    dataset: str,
    record_index: int,
    profile: dict[str, Any],
    evidence_text: str,
    findings: list[AuditFinding],
) -> None:
    candidate = profile.get("candidate") or {}
    expected_name = str(candidate.get("name") or "").strip()
    if payload.get("name") != expected_name:
        _add(findings, "error", "identity.name_mismatch", dataset, record_index, "name", "Candidate name differs from the verified profile.")

    expected_contact = dict(candidate)
    expected_contact.pop("name", None)
    if payload.get("contact") != expected_contact:
        _add(findings, "error", "identity.contact_mismatch", dataset, record_index, "contact", "Contact object differs from the verified profile.")

    if payload.get("title") not in ROLE_FAMILIES:
        _add(findings, "error", "role.unknown", dataset, record_index, "title", "Target role is outside the approved role families.")

    allowed_experiences = {
        _static_key(item, STATIC_EXPERIENCE_FIELDS) for item in profile.get("experiences") or []
    }
    for item_index, item in enumerate(payload.get("experience") or []):
        if not isinstance(item, dict) or _static_key(item, STATIC_EXPERIENCE_FIELDS) not in allowed_experiences:
            _add(findings, "error", "experience.static_mismatch", dataset, record_index, f"experience[{item_index}]", "Experience metadata is not present in the verified profile.")

    allowed_projects = {
        _static_key(item, STATIC_PROJECT_FIELDS) for item in profile.get("projects") or []
    }
    for item_index, item in enumerate(payload.get("projects") or []):
        if not isinstance(item, dict) or _static_key(item, STATIC_PROJECT_FIELDS) not in allowed_projects:
            _add(findings, "error", "project.static_mismatch", dataset, record_index, f"projects[{item_index}]", "Project metadata is not present in the verified profile.")

    allowed_skills = {str(item).strip().casefold() for item in profile.get("skills_flat") or []}
    for group_index, group in enumerate(payload.get("skills") or []):
        if not isinstance(group, dict):
            continue
        for skill in group.get("items") or []:
            if str(skill).strip().casefold() not in allowed_skills:
                _add(findings, "error", "skills.unsupported", dataset, record_index, f"skills[{group_index}]", "Generated skill is absent from the verified profile.")

    if payload.get("education") != list(profile.get("education") or []):
        _add(findings, "error", "education.static_mismatch", dataset, record_index, "education", "Education differs from the verified profile.")

    for field_name, text in _generated_prose(payload):
        if not text.strip():
            _add(findings, "warning", "prose.empty", dataset, record_index, field_name, "Generated prose is empty.")
        if len(text) > 500:
            _add(findings, "warning", "prose.too_long", dataset, record_index, field_name, "Generated prose exceeds 500 characters.")
        for number in NUMBER_PATTERN.findall(text):
            normalized_number = number.casefold().replace(" ", "")
            normalized_evidence = evidence_text.replace(" ", "")
            if normalized_number not in normalized_evidence:
                _add(findings, "warning", "prose.unverified_number", dataset, record_index, field_name, f"Numeric claim {number!r} was not found in the verified profile evidence.")


def audit_datasets(
    training_path: Path,
    holdout_path: Path,
    *,
    profile: dict[str, Any] | None = None,
) -> tuple[AuditReport, list[dict[str, Any]], list[dict[str, Any]]]:
    verified_profile = profile or load_candidate_profile()
    training = load_validated_records(training_path, min_samples=2)
    holdout = load_validated_records(holdout_path, min_samples=2)
    findings: list[AuditFinding] = []

    training_hashes = {_digest_record(record) for record in training}
    holdout_hashes = {_digest_record(record) for record in holdout}
    overlap = training_hashes & holdout_hashes
    if overlap:
        _add(findings, "error", "split.overlap", "combined", None, "messages", f"Training and holdout contain {len(overlap)} identical records.")

    evidence_text = _profile_evidence_text(verified_profile)
    names: set[str] = set()
    role_counts: Counter[str] = Counter()
    summaries: Counter[str] = Counter()
    bullets: Counter[str] = Counter()
    for dataset_name, records in (("training", training), ("holdout", holdout)):
        for index, record in enumerate(records):
            payload = _assistant_payload(record)
            names.add(str(payload.get("name") or ""))
            role_counts[str(payload.get("title") or "")] += 1
            summary = payload.get("summary")
            if isinstance(summary, str) and summary.strip():
                summaries[_normalize_text(summary)] += 1
            for field_name, bullet in _generated_prose(payload):
                if field_name == "summary":
                    continue
                if bullet.strip():
                    bullets[_normalize_text(bullet)] += 1
            _audit_record(
                payload,
                dataset=dataset_name,
                record_index=index,
                profile=verified_profile,
                evidence_text=evidence_text,
                findings=findings,
            )

    duplicate_summaries = sum(count - 1 for count in summaries.values() if count > 1)
    duplicate_bullets = sum(count - 1 for count in bullets.values() if count > 1)
    if duplicate_summaries:
        _add(findings, "warning", "duplicates.summary", "combined", None, "summary", f"Found {duplicate_summaries} repeated normalized summaries.")
    if duplicate_bullets:
        _add(findings, "warning", "duplicates.bullet", "combined", None, "bullets", f"Found {duplicate_bullets} repeated normalized bullets.")

    missing_roles = ROLE_FAMILIES - role_counts.keys()
    if missing_roles:
        _add(findings, "error", "role.missing_family", "combined", None, "title", "One or more approved role families are absent.")
    approved_counts = [role_counts[role] for role in ROLE_FAMILIES]
    if approved_counts and max(approved_counts) - min(approved_counts) > 1:
        _add(findings, "warning", "role.imbalanced", "combined", None, "title", "Approved role-family counts differ by more than one record.")

    report = AuditReport(
        created_at=datetime.now(timezone.utc).isoformat(),
        training_path=str(training_path),
        holdout_path=str(holdout_path),
        training_sha256=_digest_bytes(training_path),
        holdout_sha256=_digest_bytes(holdout_path),
        training_records=len(training),
        holdout_records=len(holdout),
        exact_overlap=len(overlap),
        unique_candidate_names=len(names),
        role_counts=dict(sorted(role_counts.items())),
        duplicate_summaries=duplicate_summaries,
        duplicate_bullets=duplicate_bullets,
        findings=findings,
    )
    return report, training, holdout


def _report_markdown(report: AuditReport) -> str:
    lines = [
        "# Fine-Tuning Dataset Audit",
        "",
        f"- Status: **{'FAIL' if report.errors else 'MANUAL REVIEW REQUIRED'}**",
        f"- Training records: {report.training_records}",
        f"- Holdout records: {report.holdout_records}",
        f"- Exact overlap: {report.exact_overlap}",
        f"- Unique candidate names: {report.unique_candidate_names}",
        f"- Duplicate summaries: {report.duplicate_summaries}",
        f"- Duplicate bullets: {report.duplicate_bullets}",
        f"- Errors: {report.errors}",
        f"- Warnings: {report.warnings}",
        "",
        "## Role counts",
        "",
    ]
    lines.extend(f"- {role}: {count}" for role, count in report.role_counts.items())
    lines.extend(["", "## Findings", ""])
    if not report.findings:
        lines.append("No automated findings.")
    else:
        lines.append("| Severity | Code | Dataset | Record | Field | Message |")
        lines.append("|---|---|---|---:|---|---|")
        for item in report.findings:
            record = "" if item.record_index is None else str(item.record_index)
            message = item.message.replace("|", "\\|")
            lines.append(f"| {item.severity} | `{item.code}` | {item.dataset} | {record} | `{item.field}` | {message} |")
    lines.extend([
        "",
        "## Manual gate",
        "",
        "Automated checks cannot prove that rewritten summaries and bullets are factually supported. Review the generated `manual_review_sample.jsonl` packet before training.",
        "",
    ])
    return "\n".join(lines)


def _manual_sample(
    training: list[dict[str, Any]], holdout: list[dict[str, Any]], seed: int = 42
) -> list[dict[str, Any]]:
    by_role: dict[str, list[dict[str, Any]]] = {role: [] for role in ROLE_FAMILIES}
    for source, records in (("training", training), ("holdout", holdout)):
        for record in records:
            payload = _assistant_payload(record)
            role = payload.get("title")
            if role in by_role:
                by_role[role].append({
                    "source": source,
                    "role": role,
                    "input": record["messages"][1]["content"],
                    "output": payload,
                    "review": {"decision": "", "unsupported_claims": [], "notes": ""},
                })
    rng = random.Random(seed)
    selected: list[dict[str, Any]] = []
    for role in sorted(ROLE_FAMILIES):
        candidates = by_role[role]
        rng.shuffle(candidates)
        selected.extend(candidates[:10])
    rng.shuffle(selected)
    return selected


def write_reports(
    report: AuditReport,
    training: list[dict[str, Any]],
    holdout: list[dict[str, Any]],
    output_dir: Path,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "dataset_audit.json").write_text(
        json.dumps(report.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (output_dir / "dataset_audit.md").write_text(_report_markdown(report), encoding="utf-8")
    with (output_dir / "manual_review_sample.jsonl").open("w", encoding="utf-8", newline="\n") as handle:
        for item in _manual_sample(training, holdout):
            handle.write(json.dumps(item, ensure_ascii=False) + "\n")
    (output_dir / "MANUAL_REVIEW_INSTRUCTIONS.md").write_text(
        "# Manual Dataset Review\n\n"
        "Review all 30 lines in `manual_review_sample.jsonl` (10 per target role). "
        "Each line includes `input`, `output`, and an empty `review` object.\n\n"
        "For every line:\n\n"
        "1. Compare each summary and bullet with your real resume/profile evidence.\n"
        "2. Set `review.decision` to `accept`, `edit`, or `reject`.\n"
        "3. List unsupported statements in `review.unsupported_claims`.\n"
        "4. Add concise correction notes in `review.notes`.\n"
        "5. Pay special attention to repeated bullets; the automated audit reports exact duplicates.\n\n"
        "Do not begin training until all 30 decisions are filled and every unsupported claim is corrected or removed.\n",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit fine-tuning datasets against the verified profile.")
    parser.add_argument("--training", default="backend/data/finetuning/training_data.jsonl")
    parser.add_argument("--holdout", default="backend/data/finetuning/holdout_eval.jsonl")
    parser.add_argument("--output-dir", default="backend/data/finetuning/reports")
    args = parser.parse_args()
    try:
        report, training, holdout = audit_datasets(Path(args.training), Path(args.holdout))
        write_reports(report, training, holdout, Path(args.output_dir))
    except (DatasetValidationError, ValueError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(
        f"Audited {report.training_records} training and {report.holdout_records} holdout records: "
        f"{report.errors} errors, {report.warnings} warnings."
    )
    print(f"Reports written to {args.output_dir}")
    return 1 if report.errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
