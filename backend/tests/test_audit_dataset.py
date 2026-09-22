import json
import sys
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from finetuning.audit_dataset import audit_datasets, write_reports  # noqa: E402


def _profile():
    return {
        "candidate": {"name": "Jane Doe", "email": "jane@example.org"},
        "skills_flat": ["Python"],
        "skills": [{"category": "Stack", "items": ["Python"]}],
        "experiences": [{
            "company": "Verified Co", "role": "Engineer", "duration": "2020 - 2024",
            "location": "Remote", "technologies": ["Python"], "evidence": ["Improved latency by 20%"],
        }],
        "projects": [{
            "name": "Verified Project", "description": "Verified description",
            "technologies": ["Python"], "link": "https://example.org/project",
        }],
        "education": [],
    }


def _record(role: str, suffix: str, *, name: str = "Jane Doe", metric: str = "20%"):
    result = {
        "name": name,
        "title": role,
        "contact": {"email": "jane@example.org"},
        "summary": f"Backend engineer with verified impact {metric}; variation {suffix}.",
        "skills": [{"category": "Verified Role-Relevant Skills", "items": ["Python"]}],
        "experience": [{
            "company": "Verified Co", "role": "Engineer", "duration": "2020 - 2024",
            "location": "Remote", "technologies": ["Python"], "bullets": [f"Improved latency by {metric} ({suffix})."],
        }],
        "projects": [{
            "name": "Verified Project", "description": "Verified description",
            "technologies": ["Python"], "bullets": [f"Built verified project {suffix}."],
            "link": "https://example.org/project",
        }],
        "education": [],
    }
    return {"messages": [
        {"role": "system", "content": "Use facts."},
        {"role": "user", "content": f"Prompt {suffix}"},
        {"role": "assistant", "content": json.dumps(result)},
    ]}


def _write(path: Path, records):
    path.write_text("".join(json.dumps(record) + "\n" for record in records), encoding="utf-8")


def test_clean_datasets_have_no_errors_and_write_review_packet(tmp_path):
    roles = ["Python Backend Developer", "React / Next.js Frontend Developer", "Figma UI/UX Designer"]
    training = tmp_path / "training.jsonl"
    holdout = tmp_path / "holdout.jsonl"
    _write(training, [_record(roles[index % 3], f"train-{index}") for index in range(30)])
    _write(holdout, [_record(roles[index % 3], f"holdout-{index}") for index in range(30)])
    report, train_records, holdout_records = audit_datasets(training, holdout, profile=_profile())
    assert report.errors == 0
    assert report.exact_overlap == 0
    output = tmp_path / "reports"
    write_reports(report, train_records, holdout_records, output)
    assert (output / "dataset_audit.json").exists()
    assert (output / "MANUAL_REVIEW_INSTRUCTIONS.md").exists()
    assert len((output / "manual_review_sample.jsonl").read_text(encoding="utf-8").splitlines()) == 30


def test_identity_and_overlap_are_hard_errors(tmp_path):
    shared = _record("Python Backend Developer", "shared", name="Wrong Name")
    training = tmp_path / "training.jsonl"
    holdout = tmp_path / "holdout.jsonl"
    _write(training, [shared, _record("React / Next.js Frontend Developer", "a")])
    _write(holdout, [shared, _record("Figma UI/UX Designer", "b")])
    report, _, _ = audit_datasets(training, holdout, profile=_profile())
    codes = {finding.code for finding in report.findings}
    assert "split.overlap" in codes
    assert "identity.name_mismatch" in codes
    assert report.errors >= 3


def test_unverified_metric_is_warning(tmp_path):
    training = tmp_path / "training.jsonl"
    holdout = tmp_path / "holdout.jsonl"
    _write(training, [_record("Python Backend Developer", "a", metric="99%"), _record("React / Next.js Frontend Developer", "b")])
    _write(holdout, [_record("Figma UI/UX Designer", "c"), _record("Python Backend Developer", "d")])
    report, _, _ = audit_datasets(training, holdout, profile=_profile())
    assert any(finding.code == "prose.unverified_number" for finding in report.findings)
