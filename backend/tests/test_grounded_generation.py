from ai.generator import ResumeGenerator, enforce_grounded_resume
from ai.prompts import STRICT_SYSTEM_PROMPT
from rag.retriever import RAGRetriever


EVIDENCE = """
=== VERIFIED WORK EXPERIENCE ACHIEVEMENTS ===
Software Intern at Bright Labs from 2025 to 2026. Built Python API validation and added automated tests.
=== VERIFIED TECHNICAL PROJECTS ===
Project: Resume Auditor. Used Python and FastAPI to validate resume records.
=== VERIFIED EDUCATION & CREDENTIALS ===
Bachelor of Computer Applications at CHRIST (Deemed to be University), 2024 - 2028.
"""


def test_grounding_filter_removes_invented_entities_and_metrics():
    generated = {
        "name": "Abbreviated Name",
        "contact": {"email": "invented@example.com"},
        "summary": "Python developer. Increased revenue by 90%.",
        "skills": [{"category": "Tools", "items": ["Python", "Kubernetes"]}],
        "experience": [
            {
                "company": "Bright Labs",
                "role": "Software Intern",
                "duration": "2025 to 2026",
                "bullets": ["Built Python API validation.", "Improved performance by 75%."],
            },
            {"company": "FakeCorp", "role": "AI Intern", "bullets": ["Created an AI platform."]},
        ],
        "projects": [
            {"name": "Resume Auditor", "description": "Used Python and FastAPI to validate resume records.", "bullets": []},
            {"name": "Autonomous Drone", "description": "Created computer vision software.", "bullets": []},
        ],
        "education": [
            {"institution": "CHRIST (Deemed to be University)", "degree": "Bachelor of Computer Applications", "year": "2024 - 2028"},
            {"institution": "Stanford University", "degree": "MSc Artificial Intelligence", "year": "2026"},
        ],
    }

    cleaned = enforce_grounded_resume(
        generated,
        EVIDENCE,
        {"name": "Joji George Alungal", "email": "joji@example.com"},
        "Python Backend Intern",
    )

    assert cleaned["name"] == "Joji George Alungal"
    assert cleaned["contact"]["email"] == "joji@example.com"
    assert cleaned["title"] == "Python Backend Intern"
    assert [item["company"] for item in cleaned["experience"]] == ["Bright Labs"]
    assert cleaned["experience"][0]["bullets"] == ["Built Python API validation."]
    assert [item["name"] for item in cleaned["projects"]] == ["Resume Auditor"]
    assert [item["institution"] for item in cleaned["education"]] == ["CHRIST (Deemed to be University)"]
    assert cleaned["skills"][0]["items"] == ["Python"]
    assert "90%" not in cleaned["summary"]
    assert cleaned["_grounding_validation"]["removed"] == {
        "experience": 1,
        "projects": 1,
        "education": 1,
        "skills": 1,
        "bullets": 1,
    }


def test_prompt_requires_omission_instead_of_plausible_fillers():
    assert "EMPTY IS CORRECT" in STRICT_SYSTEM_PROMPT
    assert "Add an internship only when both its organization and internship title are explicitly present" in STRICT_SYSTEM_PROMPT
    assert "Never guess campus, graduation date, GPA" in STRICT_SYSTEM_PROMPT


def test_retrieval_prompt_contains_raw_verified_source_excerpts():
    class EvidenceDB:
        def query(self, query_text, collection_names=None, n_results=5):
            collection = collection_names[0]
            if collection == "raw_documents":
                return [{"content": "Exact college and project text from uploaded PDF", "similarity": 0.91}]
            return []

    context = RAGRetriever(EvidenceDB()).retrieve_context_for_jd("Python internship")

    assert "=== VERIFIED SOURCE DOCUMENT EXCERPTS ===" in context["formatted_context"]
    assert "Exact college and project text from uploaded PDF" in context["formatted_context"]


def test_raw_document_profile_extracts_verified_identity_without_inventing_records(monkeypatch):
    from rag.vectorstore import ChromaManager

    manager = object.__new__(ChromaManager)
    manager.get_all_items = lambda: {
        "experiences": [],
        "projects": [],
        "skills": [],
        "education": [],
        "raw_documents": [{
            "id": "raw-1",
            "document": "JOJI A G Bachelor of Computer Applications joji@example.com • +91 9400776781 PROFESSIONAL SUMMARY Verified summary.",
            "metadata": {"title": "Resume"},
        }],
    }

    profile = manager.get_candidate_profile()
    assert profile["candidate"]["name"] == "JOJI A G"
    assert profile["candidate"]["email"] == "joji@example.com"
    assert profile["candidate"]["phone"] == "+91 9400776781"
    assert profile["experiences"] == []


def test_fallback_resume_limits_and_ranks_verified_projects(monkeypatch):
    from rag.vectorstore import vector_store

    projects = [
        {
            "name": f"Unrelated Repository {index}",
            "description": "No description provided.",
            "technologies": ["CSS"],
            "bullets": ["Repository metrics: 0 GitHub stars, 0 forks."],
        }
        for index in range(8)
    ]
    projects.extend([
        {
            "name": "Grounded Resume Builder",
            "description": "Built a FastAPI and React RAG application.",
            "technologies": ["Python", "FastAPI", "React", "ChromaDB"],
            "bullets": ["Implemented hybrid retrieval and grounded resume generation."],
        },
        {
            "name": "Application Tracker",
            "description": "Built a React dashboard with a FastAPI backend.",
            "technologies": ["React", "FastAPI", "Python"],
            "bullets": ["Added tests and database-backed application tracking."],
        },
        {
            "name": "API Test Harness",
            "description": "Tested REST APIs with Python.",
            "technologies": ["Python", "pytest"],
            "bullets": ["Automated API validation."],
        },
    ])
    monkeypatch.setattr(vector_store, "get_candidate_profile", lambda: {
        "exists": True,
        "candidate": {"name": "Verified Candidate"},
        "experiences": [],
        "projects": projects,
        "skills": [
            {"category": "Backend", "items": ["Python", "FastAPI"]},
            {"category": "Frontend", "items": ["React", "CSS"]},
        ],
        "education": [],
        "raw_documents": [],
    })

    result = ResumeGenerator()._build_fallback_resume(
        "Python FastAPI React intern building REST APIs with testing and RAG",
        "Full-Stack Engineering Intern",
        {},
        "",
    )

    assert len(result["projects"]) == 3
    assert {project["name"] for project in result["projects"]} == {
        "Grounded Resume Builder", "Application Tracker", "API Test Harness"
    }
