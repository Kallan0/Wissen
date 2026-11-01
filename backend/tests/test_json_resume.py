from json_resume import to_json_resume


def test_grounded_draft_is_converted_to_json_resume_schema():
    result = to_json_resume({
        "name": "Joji George Alungal",
        "title": "Backend Developer Intern",
        "contact": {"email": "joji@example.com", "location": "Kerala, India", "github": "github.com/joji"},
        "summary": "Verified summary.",
        "experience": [{"company": "Acme", "role": "Software Intern", "duration": "2025-01 - 2025-06", "bullets": ["Built verified APIs."]}],
        "projects": [{"name": "Resume Builder", "description": "Grounded project.", "technologies": ["Python"], "bullets": ["Added validation."], "link": "github.com/joji/resume-builder"}],
        "skills": [{"category": "Backend", "items": ["Python", "FastAPI"]}],
        "education": [{"institution": "Verified College", "degree": "BCA", "year": "2024 - 2028"}],
        "tailored_match_notes": ["Prioritized backend evidence."],
        "_ai_provider": "Groq",
    })

    assert result["basics"]["name"] == "Joji George Alungal"
    assert result["basics"]["profiles"][0]["url"] == "https://github.com/joji"
    assert result["work"][0]["name"] == "Acme"
    assert result["work"][0]["position"] == "Software Intern"
    assert result["work"][0]["startDate"] == "2025-01"
    assert result["work"][0]["highlights"] == ["Built verified APIs."]
    assert result["projects"][0]["keywords"] == ["Python"]
    assert result["skills"][0] == {"name": "Backend", "keywords": ["Python", "FastAPI"]}
    assert result["education"][0]["studyType"] == "BCA"
    assert result["custom"]["wissenPress"]["aiProvider"] == "Groq"


def test_non_iso_display_dates_are_kept_only_in_namespaced_custom_data():
    result = to_json_resume({
        "experience": [{"company": "Acme", "role": "Intern", "duration": "June to August 2025"}],
    })
    work = result["work"][0]
    assert "startDate" not in work
    assert "endDate" not in work
    assert work["custom"]["wissenPress"]["displayDate"] == "June to August 2025"
