import json
import sys
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from finetuning.training_preflight import run_preflight  # noqa: E402


def _record(index: int):
    output = {"name": "Jane Doe", "title": f"Role {index}", "contact": {}, "summary": "Verified", "skills": [], "experience": [], "projects": [], "education": []}
    return {"messages": [{"role": "system", "content": "Facts"}, {"role": "user", "content": f"Prompt {index}"}, {"role": "assistant", "content": json.dumps(output)}]}


def _write(path: Path, count: int, offset: int):
    path.write_text("".join(json.dumps(_record(index + offset)) + "\n" for index in range(count)), encoding="utf-8")


def test_preflight_validates_split_before_environment_checks(tmp_path):
    training, holdout = tmp_path / "train.jsonl", tmp_path / "holdout.jsonl"
    _write(training, 100, 0)
    _write(holdout, 20, 1000)
    report = run_preflight(training, holdout, tmp_path / "artifacts" / "adapter", min_free_gb=0)
    checks = {item["name"]: item for item in report["checks"]}
    assert checks["datasets.valid"]["status"] == "pass"
    assert checks["datasets.no_overlap"]["status"] == "pass"
    assert report["training_sha256"]


def test_preflight_reports_model_access_failure(tmp_path, monkeypatch):
    training, holdout = tmp_path / "train.jsonl", tmp_path / "holdout.jsonl"
    _write(training, 100, 0)
    _write(holdout, 20, 1000)
    monkeypatch.setattr(
        "finetuning.training_preflight.check_huggingface_model_access",
        lambda repo_id: (False, f"access denied: {repo_id}"),
    )

    report = run_preflight(
        training,
        holdout,
        tmp_path / "artifacts" / "adapter",
        min_free_gb=0,
        base_model="meta-llama/Meta-Llama-3-8B-Instruct",
    )

    checks = {item["name"]: item for item in report["checks"]}
    assert checks["model.access"] == {
        "name": "model.access",
        "status": "fail",
        "detail": "access denied: meta-llama/Meta-Llama-3-8B-Instruct",
    }
    assert report["passed"] is False
