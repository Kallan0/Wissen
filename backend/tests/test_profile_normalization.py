import pytest

from rag.profile_normalization import normalize_profile_submission


def test_raw_questionnaire_is_normalized_without_fabricated_fallbacks():
    profile = normalize_profile_submission({
        "name": "  Joji George Alungal  ",
        "title": "",
        "contact": {"email": " joji@example.com "},
        "skills_text": "Python, FastAPI, Python",
        "experience": [{"company": "Acme", "role": "Developer", "bullets": [" Built APIs ", ""]}],
        "projects": [{"name": "Resume Builder", "technologies_text": "Next.js, FastAPI"}],
        "education": [],
    })

    assert profile["name"] == "Joji George Alungal"
    assert profile["title"] == ""
    assert profile["skills"][0]["items"] == ["Python", "FastAPI", "Python"]
    assert profile["experience"][0]["company"] == "Acme"
    assert profile["projects"][0]["technologies"] == ["Next.js", "FastAPI"]
    serialized = str(profile)
    assert "Software Engineer" not in serialized
    assert "Organization" not in serialized


@pytest.mark.parametrize(
    "payload,error",
    [
        ({"name": ""}, "Full name"),
        ({"name": "Joji", "experience": [{"role": "Developer"}]}, "company and role"),
        ({"name": "Joji", "projects": [{"description": "Missing name"}]}, "project must include a name"),
        ({"name": "Joji", "education": [{"degree": "BSc"}]}, "institution and degree"),
    ],
)
def test_incomplete_factual_records_are_rejected(payload, error):
    with pytest.raises(ValueError, match=error):
        normalize_profile_submission(payload)
