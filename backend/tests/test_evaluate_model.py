import sys
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from finetuning.evaluate_model import summarize_results  # noqa: E402


def test_summary_counts_parse_and_schema_failures():
    profile = {
        "candidate": {"name": "Jane Doe", "email": "jane@example.org"},
        "skills_flat": [], "skills": [], "experiences": [], "projects": [], "education": [],
    }
    valid = {
        "name": "Jane Doe", "title": "Python Backend Developer",
        "contact": {"email": "jane@example.org"}, "summary": "Verified engineer.",
        "skills": [], "experience": [], "projects": [], "education": [],
    }
    summary = summarize_results(
        [{"parsed": valid, "latency_ms": 10}, {"parsed": None, "latency_ms": 20}], profile
    )
    assert summary["total"] == 2
    assert summary["parse_rate"] == 0.5
    assert summary["schema_valid_rate"] == 0.5
    assert summary["failed_records"] == 1
    assert summary["errors"] == 1
