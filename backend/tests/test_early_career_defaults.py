from pathlib import Path

from ai.prompts import ROLE_RECOMMENDATION_PROMPT


ROOT = Path(__file__).resolve().parents[2]


def test_role_recommendation_prompt_is_limited_to_early_career_roles():
    assert "Recommend only Internship, Graduate, Trainee, Junior, or Entry-Level roles" in ROLE_RECOMMENDATION_PROMPT
    assert '"seniority": "Internship | Graduate | Trainee | Junior | Entry-Level"' in ROLE_RECOMMENDATION_PROMPT
    assert "Never recommend Senior, Lead, Staff, Principal, Architect" in ROLE_RECOMMENDATION_PROMPT


def test_job_tailor_presets_are_internship_level():
    source = (ROOT / "frontend" / "src" / "components" / "JobTailor.tsx").read_text(encoding="utf-8")
    preset_block = source.split("const SAMPLE_JDS = [", 1)[1].split("];", 1)[0]

    assert "AI & RAG Engineering Intern" in preset_block
    assert "Python Backend Intern" in preset_block
    assert "Frontend & UI/UX Intern" in preset_block
    assert "4+ years" not in preset_block
    assert "Senior" not in preset_block
