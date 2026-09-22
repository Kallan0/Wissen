import json
import sys
from pathlib import Path

import pytest


BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from finetuning.finetune_llama3 import (  # noqa: E402
    DatasetValidationError,
    load_validated_records,
    split_records,
)


def _sample(index: int, name: str = "Jane Doe") -> dict:
    result = {
        "name": name,
        "title": f"Engineer {index}",
        "contact": {"email": f"jane{index}@example.org"},
        "summary": "Verified background only.",
        "skills": [],
        "experience": [],
        "projects": [],
        "education": [],
    }
    return {
        "messages": [
            {"role": "system", "content": "Use verified facts only."},
            {"role": "user", "content": f"Tailor resume for role {index}."},
            {"role": "assistant", "content": json.dumps(result)},
        ]
    }


def _write_jsonl(path: Path, records: list[dict]) -> None:
    path.write_text("".join(json.dumps(item) + "\n" for item in records), encoding="utf-8")


def test_validation_deduplicates_and_split_is_reproducible(tmp_path):
    dataset = tmp_path / "training.jsonl"
    records = [_sample(index) for index in range(10)]
    _write_jsonl(dataset, records + [records[0]])

    loaded = load_validated_records(dataset, min_samples=10)
    assert len(loaded) == 10
    assert split_records(loaded, 0.2, 42) == split_records(loaded, 0.2, 42)
    train, evaluation = split_records(loaded, 0.2, 42)
    assert len(train) == 8
    assert len(evaluation) == 2


def test_validation_rejects_placeholder_identity(tmp_path):
    dataset = tmp_path / "training.jsonl"
    _write_jsonl(dataset, [_sample(1, name="Alex Chen"), _sample(2)])

    with pytest.raises(DatasetValidationError, match="placeholder/synthetic"):
        load_validated_records(dataset, min_samples=2)


def test_validation_rejects_non_json_assistant(tmp_path):
    dataset = tmp_path / "training.jsonl"
    record = _sample(1)
    record["messages"][-1]["content"] = "not-json"
    _write_jsonl(dataset, [record, _sample(2)])

    with pytest.raises(DatasetValidationError, match="assistant content is not valid JSON"):
        load_validated_records(dataset, min_samples=2)
