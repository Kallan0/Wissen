import json
import sys
from pathlib import Path

import pytest


BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from finetuning import dataset_generator  # noqa: E402
from finetuning.split_dataset import split_dataset  # noqa: E402


def _sample(index: int) -> dict:
    output = {
        "name": "Jane Doe",
        "title": f"Role {index}",
        "contact": {"email": "jane@example.org"},
        "summary": f"Verified summary {index}.",
        "skills": [],
        "experience": [{"company": "Verified Co", "role": "Engineer", "bullets": []}],
        "projects": [],
        "education": [],
    }
    return {
        "messages": [
            {"role": "system", "content": "Use verified facts only."},
            {"role": "user", "content": f"Tailor variation {index}."},
            {"role": "assistant", "content": json.dumps(output)},
        ]
    }


def test_profile_without_name_is_rejected(monkeypatch):
    monkeypatch.setattr(
        dataset_generator.vector_store,
        "get_candidate_profile",
        lambda: {"exists": True, "candidate": {}, "experiences": [{"role": "Engineer"}]},
    )
    with pytest.raises(ValueError, match="candidate name is missing"):
        dataset_generator.load_candidate_profile()


def test_profile_without_experience_is_rejected(monkeypatch):
    monkeypatch.setattr(
        dataset_generator.vector_store,
        "get_candidate_profile",
        lambda: {"exists": True, "candidate": {"name": "Jane Doe"}, "experiences": []},
    )
    with pytest.raises(ValueError, match="experience is missing"):
        dataset_generator.load_candidate_profile()


def test_verified_name_overrides_model_output():
    profile = {"candidate": {"name": "Joji George Alungal"}}
    generated = {"name": "Joji G. Alungal", "summary": "Verified summary."}
    result = dataset_generator._inject_verified_name(generated, profile)
    assert result is not None
    assert result["name"] == "Joji George Alungal"


def test_profile_chunks_are_deduplicated(monkeypatch):
    monkeypatch.setattr(
        dataset_generator.vector_store,
        "get_candidate_profile",
        lambda: {
            "exists": True,
            "candidate": {"name": "Jane Doe"},
            "experiences": [
                {"company": "Verified Co", "role": "Engineer", "content": "Built APIs", "technologies": ["Python"]},
                {"company": "Verified Co", "role": "Engineer", "content": "Improved tests", "technologies": ["FastAPI"]},
            ],
            "projects": [
                {"name": "Portal", "description": "Short", "technologies": ["React"]},
                {"name": "Portal", "description": "A longer verified description", "technologies": ["Next.js"]},
            ],
            "skills": [{"category": "Stack", "items": ["Python", "React"]}],
        },
    )
    profile = dataset_generator.load_candidate_profile()
    assert len(profile["experiences"]) == 1
    assert profile["experiences"][0]["evidence"] == ["Built APIs", "Improved tests"]
    assert len(profile["projects"]) == 1
    assert profile["projects"][0]["description"] == "A longer verified description"
    assert profile["projects"][0]["technologies"] == ["React", "Next.js"]


def test_static_identity_and_employment_are_assembled_by_python():
    role = dataset_generator.ROLE_FAMILIES[0]
    profile = {
        "candidate": {"name": "Joji George Alungal", "email": "verified@example.org"},
        "skills_flat": ["Python", "FastAPI"],
        "experiences": [{
            "company": "Verified Co", "role": "Engineer", "duration": "2024 - Present",
            "location": "Remote", "technologies": ["Python"], "evidence": ["Built APIs"],
        }],
        "projects": [{
            "name": "Verified Project", "description": "Verified description",
            "technologies": ["FastAPI"], "link": "https://example.org/project",
        }],
        "education": [],
    }
    generated = {
        "summary": "Grounded backend engineer.",
        "experience_bullets": [{"index": 0, "bullets": ["Built verified APIs."]}],
        "project_bullets": [{"index": 0, "bullets": ["Implemented the verified service."]}],
        "tailored_match_notes": ["Prioritized Python evidence."],
        "name": "Wrong Name",
    }
    result = dataset_generator._assemble_verified_resume(generated, profile, role)
    assert result["name"] == "Joji George Alungal"
    assert result["contact"]["email"] == "verified@example.org"
    assert result["experience"][0]["company"] == "Verified Co"
    assert result["projects"][0]["name"] == "Verified Project"


def test_split_is_deterministic_and_80_20(tmp_path):
    source = tmp_path / "generated.jsonl"
    source.write_text(
        "".join(json.dumps(_sample(index)) + "\n" for index in range(100)),
        encoding="utf-8",
    )
    train = tmp_path / "training_data.jsonl"
    holdout = tmp_path / "holdout_eval.jsonl"
    counts = split_dataset(source, train, holdout, seed=42)
    assert counts == (80, 20)
    train_lines = train.read_text(encoding="utf-8").splitlines()
    holdout_lines = holdout.read_text(encoding="utf-8").splitlines()
    assert len(train_lines) == 80
    assert len(holdout_lines) == 20
    assert set(train_lines).isdisjoint(holdout_lines)
