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
    assert profile["skills"][0]["items"] == ["Python", "FastAPI"]
    assert profile["experience"][0]["company"] == "Acme"
    assert profile["projects"][0]["technologies"] == ["Next.js", "FastAPI"]
    serialized = str(profile)
    assert "Software Engineer" not in serialized
    assert "Organization" not in serialized


def test_duplicate_profile_entities_are_merged_before_ingestion():
    profile = normalize_profile_submission({
        "name": "Joji George Alungal",
        "experience": [
            {"company": "Acme", "role": "Intern", "duration": "2025", "bullets": ["Built APIs"]},
            {"company": "ACME", "role": "Intern", "duration": "2025", "bullets": ["Built APIs", "Added tests"]},
        ],
        "projects": [
            {"name": "Resume Builder", "highlights": ["Created PDF export"]},
            {"name": "resume-builder", "highlights": ["Created PDF export", "Added RAG"]},
        ],
    })

    assert len(profile["experience"]) == 1
    assert profile["experience"][0]["bullets"] == ["Built APIs", "Added tests"]
    assert len(profile["projects"]) == 1
    assert profile["projects"][0]["highlights"] == ["Created PDF export", "Added RAG"]


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


@pytest.mark.parametrize(
    "payload,section",
    [
        ({"experience": [{"company": "Acme", "role": "Intern"}]}, "experience"),
        ({"projects": [{"name": "Portfolio"}]}, "projects"),
        ({"education": [{"institution": "Example University", "degree": "BCA"}]}, "education"),
    ],
)
def test_existing_profile_can_accept_one_section_without_identity(payload, section):
    profile = normalize_profile_submission(payload, require_identity=False)

    assert profile["name"] == ""
    assert len(profile[section]) == 1


def test_existing_profile_update_cannot_be_empty():
    with pytest.raises(ValueError, match="Add at least one"):
        normalize_profile_submission({}, require_identity=False)

    with pytest.raises(ValueError, match="Add at least one"):
        normalize_profile_submission({"title": "Intern"}, require_identity=False)


def test_existing_profile_can_update_contact_without_resubmitting_name():
    profile = normalize_profile_submission(
        {"contact": {"github": "https://github.com/example"}},
        require_identity=False,
    )

    assert profile["name"] == ""
    assert profile["contact"]["github"] == "https://github.com/example"
