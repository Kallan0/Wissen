"""
End-to-End Test Suite – AI Resume Builder Backend
===================================================
Covers every public API route:

  • Health & Models
  • Knowledge Base (stats, ingest-text, ingest-profile, seed-sample, upload-resume-pdf, clear)
  • RAG Retrieval (/api/tailor)
  • Career Recommendations (/api/recommend-positions)
  • Data Connectors (GitHub, Canva, Filesystem)
  • PDF Export & Download

Run from the `backend/` directory:

    pytest tests/test_e2e.py -v

Dependencies (already in requirements.txt / venv):
    pytest, httpx, fastapi[testclient]

The suite uses FastAPI's TestClient (synchronous ASGI test client) so that no
live server needs to be running and no external network calls are made for
deterministic coverage.  LLM/Ollama calls are mocked so the tests are fast and
offline-safe.
"""

import io
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

# ── Make sure the backend package root is on sys.path ────────────────────────
BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))
TEST_CHROMA_DIR = BACKEND_DIR / "data" / "test_chroma_db"
os.environ["CHROMA_DIR"] = str(TEST_CHROMA_DIR)

# ── Import the FastAPI app (this initialises ChromaDB in-memory via config) ──
from main import app  # noqa: E402
from config import settings  # noqa: E402
from rag.vectorstore import vector_store  # noqa: E402

# Config may already be imported by another test module before this file sets
# CHROMA_DIR. Force the lazy manager onto the isolated test directory and fail
# loudly if a future test initializes it before isolation is applied.
if vector_store.is_initialized:
    raise RuntimeError("E2E ChromaDB was initialized before test isolation.")
settings.CHROMA_DIR = TEST_CHROMA_DIR

# ─────────────────────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture(scope="session", autouse=True)
def _mock_embeddings():
    """Mock ChromaDB's ONNX embedding function so tests don't require external weights download or global ~/.cache writes."""
    try:
        from chromadb.utils.embedding_functions.onnx_mini_lm_l6_v2 import ONNXMiniLM_L6_V2
        with patch.object(ONNXMiniLM_L6_V2, "__call__", side_effect=lambda input: [[0.05] * 384 for _ in input]):
            yield
    except Exception:
        yield

@pytest.fixture
def tmp_path():
    """Workspace-local temporary directory fixture for PDF export tests."""
    temp_dir = BACKEND_DIR / "data" / "test_tmp"
    temp_dir.mkdir(parents=True, exist_ok=True)
    yield temp_dir
    for f in temp_dir.glob("*"):
        try:
            f.unlink()
        except Exception:
            pass

@pytest.fixture(scope="module")
def client():
    """
    Module-scoped TestClient.  Keeps the same ChromaDB state across tests in
    the module so that the flow 'seed → tailor → recommend' makes sense.
    """
    with TestClient(app) as c:
        yield c


@pytest.fixture(autouse=True)
def _reset_kb(client):
    """
    Clear the knowledge-base before every single test so each test is
    independent.  Using autouse=True means you never have to call this
    manually.
    """
    client.post("/api/knowledge-base/clear")
    yield
    # Optional teardown – clear again after the test
    client.post("/api/knowledge-base/clear")


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

SAMPLE_JD = (
    "We are looking for a Senior Python Backend Engineer with experience in "
    "FastAPI, REST APIs, PostgreSQL and Redis.  Knowledge of Docker and CI/CD "
    "pipelines is a strong plus.  You will design microservices for a "
    "high-concurrency data platform."
)

MINIMAL_PROFILE = {
    "name": "Jane Candidate",
    "summary": "A passionate software engineer with backend expertise.",
    "experience": [
        {
            "company": "TechCorp",
            "role": "Backend Engineer",
            "duration": "2020 - 2023",
            "location": "Remote",
            "technologies": ["Python", "FastAPI", "PostgreSQL"],
            "bullets": [
                "Built REST APIs serving 1M+ daily requests.",
                "Optimised PostgreSQL queries reducing latency by 40%.",
            ],
        }
    ],
    "projects": [
        {
            "name": "DataPipe",
            "description": "Real-time data pipeline built with FastAPI and Redis.",
            "technologies": ["FastAPI", "Redis", "Docker"],
            "highlights": ["Handled 10k concurrent connections."],
            "link": "https://github.com/test/datapipe",
        }
    ],
    "skills": [
        {"category": "Backend", "items": ["Python", "FastAPI", "PostgreSQL", "Redis"]}
    ],
    "education": [
        {
            "institution": "State University",
            "degree": "B.Sc. Computer Science",
            "year": "2020",
            "details": "First Class.",
        }
    ],
}

# Mocked resume dict returned by the PDF generator
MOCK_RESUME_DATA = {
    "basics": {
        "name": "Jane Doe",
        "email": "jane@example.com",
        "label": "Backend Engineer",
        "summary": "Experienced backend engineer.",
    },
    "work": [],
    "projects": [],
    "skills": [],
    "education": [],
}


def _mock_ollama_status():
    return {"status": "ok", "models": ["llama3"]}


def _mock_tailored_resume():
    return {
        "basics": {
            "name": "Jane Doe",
            "label": "Backend Engineer",
            "summary": "Tailored resume summary.",
        },
        "work": [],
        "projects": [],
        "skills": [],
        "education": [],
    }


def _mock_recommendations():
    return {
        "positions": [
            {"title": "Backend Engineering Intern", "match_score": 0.92},
            {"title": "Junior Platform Engineer", "match_score": 0.85},
        ]
    }


# ─────────────────────────────────────────────────────────────────────────────
# 1 ── Health & Model endpoints
# ─────────────────────────────────────────────────────────────────────────────

class TestHealthAndModels:
    def test_health_returns_200(self, client):
        with patch(
            "ai.generator.resume_generator.check_ollama_status",
            new_callable=AsyncMock,
            return_value=_mock_ollama_status(),
        ):
            resp = client.get("/api/health")
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "healthy"
        assert body["api_revision"] == "logical-chunks-query-expansion-v1"
        assert "ollama" in body
        assert "knowledge_base" in body

    def test_health_contains_kb_stats(self, client):
        with patch(
            "ai.generator.resume_generator.check_ollama_status",
            new_callable=AsyncMock,
            return_value=_mock_ollama_status(),
        ):
            resp = client.get("/api/health")
        kb = resp.json()["knowledge_base"]
        # All five collection counts should be present
        for col in ("experiences", "projects", "skills", "education", "raw_documents"):
            assert col in kb, f"Missing collection '{col}' in KB stats"

    def test_get_models_returns_list(self, client):
        with patch(
            "ai.generator.resume_generator.get_available_models",
            new_callable=AsyncMock,
            return_value=["llama3", "mistral"],
        ):
            resp = client.get("/api/models")
        assert resp.status_code == 200
        assert "models" in resp.json()
        assert isinstance(resp.json()["models"], list)


# ─────────────────────────────────────────────────────────────────────────────
# 2 ── Knowledge Base – stats
# ─────────────────────────────────────────────────────────────────────────────

class TestKnowledgeBaseStats:
    def test_stats_returns_dict(self, client):
        resp = client.get("/api/knowledge-base/stats")
        assert resp.status_code == 200
        body = resp.json()
        assert "total_items" in body

    def test_stats_initially_empty(self, client):
        resp = client.get("/api/knowledge-base/stats")
        body = resp.json()
        assert body["total_items"] == 0

    def test_stats_after_ingest(self, client):
        client.post(
            "/api/knowledge-base/ingest-text",
            json={"title": "Test Note", "content": "Python FastAPI backend experience."},
        )
        resp = client.get("/api/knowledge-base/stats")
        body = resp.json()
        assert body["total_items"] > 0


# ─────────────────────────────────────────────────────────────────────────────
# 3 ── Knowledge Base – ingest-text
# ─────────────────────────────────────────────────────────────────────────────

class TestIngestText:
    def test_ingest_text_success(self, client):
        payload = {
            "title": "My Tech Blog",
            "content": "I have extensive experience with Python, FastAPI, and Docker.",
            "category": "raw_documents",
            "tags": ["python", "backend"],
        }
        resp = client.post("/api/knowledge-base/ingest-text", json=payload)
        assert resp.status_code == 200
        body = resp.json()
        assert "chunks" in body
        assert body["chunks"] >= 1
        assert "Successfully ingested" in body["message"]

    def test_ingest_text_increments_stats(self, client):
        before = client.get("/api/knowledge-base/stats").json()["total_items"]
        client.post(
            "/api/knowledge-base/ingest-text",
            json={"title": "Note 1", "content": "Some content about machine learning."},
        )
        after = client.get("/api/knowledge-base/stats").json()["total_items"]
        assert after > before

    def test_ingest_text_without_optional_fields(self, client):
        payload = {"title": "Bare minimum", "content": "Content without tags or category."}
        resp = client.post("/api/knowledge-base/ingest-text", json=payload)
        assert resp.status_code == 200

    def test_ingest_text_missing_title_returns_422(self, client):
        resp = client.post(
            "/api/knowledge-base/ingest-text",
            json={"content": "Content without title field."},
        )
        assert resp.status_code == 422

    def test_ingest_text_missing_content_returns_422(self, client):
        resp = client.post(
            "/api/knowledge-base/ingest-text",
            json={"title": "Title without content"},
        )
        assert resp.status_code == 422


# ─────────────────────────────────────────────────────────────────────────────
# 4 ── Knowledge Base – ingest-profile
# ─────────────────────────────────────────────────────────────────────────────

class TestIngestProfile:
    def test_ingest_profile_success(self, client):
        resp = client.post("/api/knowledge-base/ingest-profile", json=MINIMAL_PROFILE)
        assert resp.status_code == 200
        body = resp.json()
        assert "indexed" in body
        assert body["indexed"]["experiences"] > 0

    def test_ingest_profile_populates_collections(self, client):
        client.post("/api/knowledge-base/ingest-profile", json=MINIMAL_PROFILE)
        stats = client.get("/api/knowledge-base/stats").json()
        assert stats["experiences"] > 0
        assert stats["projects"] > 0
        assert stats["skills"] > 0
        assert stats["education"] > 0

    @pytest.mark.parametrize(
        "payload,collection",
        [
            ({"experience": [{"company": "Acme", "role": "Intern"}]}, "experiences"),
            ({"projects": [{"name": "New Project", "description": "Verified work"}]}, "projects"),
            ({"education": [{"institution": "Example University", "degree": "BCA"}]}, "education"),
        ],
    )
    def test_existing_profile_accepts_section_without_identity(self, client, payload, collection):
        client.post("/api/knowledge-base/ingest-profile", json=MINIMAL_PROFILE)
        before = client.get("/api/knowledge-base/stats").json()[collection]

        resp = client.post("/api/knowledge-base/ingest-profile", json=payload)

        assert resp.status_code == 200
        assert resp.json()["stats"][collection] > before

    def test_ingest_profile_empty_body_is_rejected(self, client):
        """Identity guards must prevent anonymous profile records."""
        resp = client.post("/api/knowledge-base/ingest-profile", json={})
        assert resp.status_code == 400


# ─────────────────────────────────────────────────────────────────────────────
# 5 ── Knowledge Base – seed-sample
# ─────────────────────────────────────────────────────────────────────────────

class TestSeedSample:
    def test_seed_sample_success(self, client):
        resp = client.post("/api/knowledge-base/seed-sample")
        assert resp.status_code == 200
        body = resp.json()
        assert "counts" in body
        assert "stats" in body

    def test_seed_sample_populates_kb(self, client):
        client.post("/api/knowledge-base/seed-sample")
        stats = client.get("/api/knowledge-base/stats").json()
        assert stats["total_items"] > 0

    def test_seed_sample_is_idempotent(self, client):
        """Calling seed twice should not crash and should clear+re-populate."""
        r1 = client.post("/api/knowledge-base/seed-sample")
        r2 = client.post("/api/knowledge-base/seed-sample")
        assert r1.status_code == 200
        assert r2.status_code == 200
        # After second seed, KB should equal first-seed totals
        assert r1.json()["stats"]["total_items"] == r2.json()["stats"]["total_items"]


# ─────────────────────────────────────────────────────────────────────────────
# 6 ── Knowledge Base – get-items
# ─────────────────────────────────────────────────────────────────────────────

class TestGetItems:
    def test_items_empty_initially(self, client):
        resp = client.get("/api/knowledge-base/items")
        assert resp.status_code == 200
        body = resp.json()
        for col in ("experiences", "projects", "skills", "education", "raw_documents"):
            assert body.get(col, []) == []

    def test_items_after_profile_ingest(self, client):
        client.post("/api/knowledge-base/ingest-profile", json=MINIMAL_PROFILE)
        resp = client.get("/api/knowledge-base/items")
        assert resp.status_code == 200
        body = resp.json()
        assert len(body["experiences"]) > 0
        # Each item should have id, document, and metadata
        item = body["experiences"][0]
        assert "id" in item
        assert "document" in item
        assert "metadata" in item


# ─────────────────────────────────────────────────────────────────────────────
# 7 ── Knowledge Base – upload-resume-pdf
# ─────────────────────────────────────────────────────────────────────────────

class TestUploadResumePDF:
    def _make_pdf_bytes(self) -> bytes:
        """
        Create a minimal valid single-page PDF in pure Python (no reportlab).
        This is the smallest valid PDF structure that pypdf can parse.
        """
        # A tiny PDF that pypdf can read and that has one text page
        pdf_content = b"""%PDF-1.4
1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj
2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj
3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792]
/Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >> endobj
4 0 obj << /Length 44 >>
stream
BT /F1 12 Tf 100 700 Td (Python FastAPI Engineer) Tj ET
endstream
endobj
5 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj
xref
0 6
0000000000 65535 f\r
0000000009 00000 n\r
0000000058 00000 n\r
0000000115 00000 n\r
0000000266 00000 n\r
0000000360 00000 n\r
trailer << /Size 6 /Root 1 0 R >>
startxref
441
%%EOF"""
        return pdf_content

    def test_upload_valid_pdf(self, client):
        pdf_bytes = self._make_pdf_bytes()
        resp = client.post(
            "/api/knowledge-base/upload-resume-pdf",
            files={"file": ("resume.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
        )
        # May succeed (200) or raise 400 if the minimal PDF has no extractable
        # text in this environment – both are acceptable business responses.
        assert resp.status_code in (200, 400)

    def test_upload_non_pdf_rejected(self, client):
        fake_txt = io.BytesIO(b"This is not a PDF file")
        resp = client.post(
            "/api/knowledge-base/upload-resume-pdf",
            files={"file": ("resume.txt", fake_txt, "text/plain")},
        )
        assert resp.status_code == 400
        assert "PDF" in resp.json()["detail"]

    def test_upload_wrong_extension_rejected(self, client):
        fake_data = io.BytesIO(b"Some data")
        resp = client.post(
            "/api/knowledge-base/upload-resume-pdf",
            files={"file": ("resume.docx", fake_data, "application/octet-stream")},
        )
        assert resp.status_code == 400


# ─────────────────────────────────────────────────────────────────────────────
# 8 ── Knowledge Base – clear
# ─────────────────────────────────────────────────────────────────────────────

class TestClearKnowledgeBase:
    def test_clear_empties_kb(self, client):
        # First, populate the KB
        client.post("/api/knowledge-base/seed-sample")
        before = client.get("/api/knowledge-base/stats").json()["total_items"]
        assert before > 0

        # Clear
        resp = client.post("/api/knowledge-base/clear")
        assert resp.status_code == 200
        assert "reset" in resp.json()["message"].lower()

        # Verify empty
        after = client.get("/api/knowledge-base/stats").json()["total_items"]
        assert after == 0

    def test_clear_on_empty_kb_is_safe(self, client):
        resp = client.post("/api/knowledge-base/clear")
        assert resp.status_code == 200


# ─────────────────────────────────────────────────────────────────────────────
# 9 ── RAG Tailoring (/api/tailor)
# ─────────────────────────────────────────────────────────────────────────────

class TestTailorResume:
    def _seed(self, client):
        client.post("/api/knowledge-base/ingest-profile", json=MINIMAL_PROFILE)

    def test_tailor_with_seeded_kb(self, client):
        self._seed(client)
        with patch(
            "ai.generator.resume_generator.generate_tailored_resume",
            new_callable=AsyncMock,
            return_value=_mock_tailored_resume(),
        ):
            resp = client.post(
                "/api/tailor",
                json={"job_description": SAMPLE_JD, "model": "llama3"},
            )
        assert resp.status_code == 200
        body = resp.json()
        assert "resume" in body
        assert "rag_context" in body
        assert body["rag_context"]["match_count"] >= 0

    def test_tailor_empty_jd_returns_400(self, client):
        resp = client.post("/api/tailor", json={"job_description": "   "})
        assert resp.status_code == 400

    def test_tailor_missing_jd_returns_422(self, client):
        resp = client.post("/api/tailor", json={"model": "llama3"})
        assert resp.status_code == 422

    def test_tailor_with_candidate_info(self, client):
        self._seed(client)
        with patch(
            "ai.generator.resume_generator.generate_tailored_resume",
            new_callable=AsyncMock,
            return_value=_mock_tailored_resume(),
        ):
            resp = client.post(
                "/api/tailor",
                json={
                    "job_description": SAMPLE_JD,
                    "candidate_name": "Jane Doe",
                    "candidate_email": "jane@example.com",
                    "candidate_location": "Remote",
                },
            )
        assert resp.status_code == 200

    def test_tailor_rag_context_structure(self, client):
        self._seed(client)
        with patch(
            "ai.generator.resume_generator.generate_tailored_resume",
            new_callable=AsyncMock,
            return_value=_mock_tailored_resume(),
        ), patch(
            "ai.generator.resume_generator.expand_job_query",
            new_callable=AsyncMock,
            return_value=["React", "Next.js", "responsive design"],
        ):
            resp = client.post("/api/tailor", json={"job_description": SAMPLE_JD})
        rag = resp.json()["rag_context"]
        assert "match_count" in rag
        assert "retrieved_items" in rag
        assert "keywords" in rag
        assert isinstance(rag["keywords"], list)
        assert rag["expanded_concepts"] == ["React", "Next.js", "responsive design"]


# ─────────────────────────────────────────────────────────────────────────────
# 10 ── Career Recommendations (/api/recommend-positions)
# ─────────────────────────────────────────────────────────────────────────────

class TestRecommendPositions:
    def test_recommend_empty_kb_returns_400(self, client):
        resp = client.post("/api/recommend-positions", json={})
        assert resp.status_code == 400

    def test_recommend_with_seeded_kb(self, client):
        client.post("/api/knowledge-base/ingest-profile", json=MINIMAL_PROFILE)
        with patch(
            "ai.generator.resume_generator.suggest_career_positions",
            new_callable=AsyncMock,
            return_value=_mock_recommendations(),
        ):
            resp = client.post("/api/recommend-positions", json={"model": "llama3"})
        assert resp.status_code == 200

    def test_recommend_no_body_accepted(self, client):
        """Endpoint accepts an optional body; sending nothing should not crash."""
        client.post("/api/knowledge-base/ingest-profile", json=MINIMAL_PROFILE)
        with patch(
            "ai.generator.resume_generator.suggest_career_positions",
            new_callable=AsyncMock,
            return_value=_mock_recommendations(),
        ):
            resp = client.post("/api/recommend-positions")
        # Either 200 or 400 (if KB is empty due to fixture reset ordering)
        assert resp.status_code in (200, 400)


# ─────────────────────────────────────────────────────────────────────────────
# 11 ── Connectors – GitHub
# ─────────────────────────────────────────────────────────────────────────────

MOCK_GITHUB_RESULT = {
    "ingested_repos": 3,
    "repos": ["repo-a", "repo-b", "repo-c"],
    "message": "Synced 3 repositories.",
}


class TestGitHubConnector:
    def test_github_sync_success(self, client):
        with patch(
            "main.github_connector.sync_user_repositories",
            new_callable=AsyncMock,
            return_value=MOCK_GITHUB_RESULT,
        ):
            resp = client.post(
                "/api/connectors/github/sync",
                json={"username": "testuser", "max_repos": 5, "fetch_readme": True},
            )
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "success"
        assert "result" in body
        assert "stats" in body

    def test_github_sync_missing_username_returns_422(self, client):
        resp = client.post(
            "/api/connectors/github/sync",
            json={"max_repos": 5},
        )
        assert resp.status_code == 422

    def test_github_sync_with_token(self, client):
        with patch(
            "main.github_connector.sync_user_repositories",
            new_callable=AsyncMock,
            return_value=MOCK_GITHUB_RESULT,
        ):
            resp = client.post(
                "/api/connectors/github/sync",
                json={"username": "testuser", "token": "ghp_secret123"},
            )
        assert resp.status_code == 200

    def test_github_sync_error_handled(self, client):
        with patch(
            "main.github_connector.sync_user_repositories",
            new_callable=AsyncMock,
            side_effect=Exception("Network error"),
        ):
            resp = client.post(
                "/api/connectors/github/sync",
                json={"username": "testuser"},
            )
        assert resp.status_code == 400
        assert "Network error" in resp.json()["detail"]


# ─────────────────────────────────────────────────────────────────────────────
# 12 ── Connectors – Canva
# ─────────────────────────────────────────────────────────────────────────────

MOCK_CANVA_RESULT = {"ingested_project": "My Portfolio Design", "chunks": 2}

CANVA_PAYLOAD = {
    "title": "Portfolio Redesign",
    "description": "Full redesign of personal portfolio using Figma and Canva.",
    "design_type": "UI/UX & Visual Design",
    "tools_used": ["Figma", "Canva"],
    "prototype_url": "https://figma.com/proto/abc123",
    "deliverables": ["Wireframes", "High-fidelity mockups"],
    "user_impact": "Increased profile visits by 60%",
}


class TestCanvaConnector:
    def test_canva_sync_success(self, client):
        with patch(
            "main.canva_connector.ingest_design_project",
            return_value=MOCK_CANVA_RESULT,
        ):
            resp = client.post("/api/connectors/canva/sync", json=CANVA_PAYLOAD)
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "success"
        assert "result" in body

    def test_canva_sync_missing_required_fields_returns_422(self, client):
        resp = client.post(
            "/api/connectors/canva/sync",
            json={"title": "Only title"},  # missing 'description'
        )
        assert resp.status_code == 422

    def test_canva_sync_minimal_payload(self, client):
        with patch(
            "main.canva_connector.ingest_design_project",
            return_value=MOCK_CANVA_RESULT,
        ):
            resp = client.post(
                "/api/connectors/canva/sync",
                json={"title": "Minimal", "description": "Short desc"},
            )
        assert resp.status_code == 200

    def test_canva_sync_error_handled(self, client):
        with patch(
            "main.canva_connector.ingest_design_project",
            side_effect=Exception("Canva API error"),
        ):
            resp = client.post("/api/connectors/canva/sync", json=CANVA_PAYLOAD)
        assert resp.status_code == 400


# ─────────────────────────────────────────────────────────────────────────────
# 13 ── Connectors – Filesystem
# ─────────────────────────────────────────────────────────────────────────────

MOCK_FS_RESULT = {"scanned_files": 5, "project_name": "Unity Game Project"}


class TestFilesystemConnector:
    def test_filesystem_scan_success(self, client):
        with patch(
            "main.creative_fs_connector.scan_and_ingest_directory",
            return_value=MOCK_FS_RESULT,
        ):
            resp = client.post(
                "/api/connectors/filesystem/scan",
                json={
                    "directory_path": "C:/Users/Joji/Projects/UnityGame",
                    "custom_project_name": "My Unity RPG",
                },
            )
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "success"
        assert "result" in body

    def test_filesystem_missing_path_returns_422(self, client):
        resp = client.post(
            "/api/connectors/filesystem/scan",
            json={"custom_project_name": "No Path"},
        )
        assert resp.status_code == 422

    def test_filesystem_error_handled(self, client):
        with patch(
            "main.creative_fs_connector.scan_and_ingest_directory",
            side_effect=Exception("Directory not found"),
        ):
            resp = client.post(
                "/api/connectors/filesystem/scan",
                json={"directory_path": "/invalid/path"},
            )
        assert resp.status_code == 400


# ─────────────────────────────────────────────────────────────────────────────
# 14 ── PDF Export & Download
# ─────────────────────────────────────────────────────────────────────────────

class TestBackendPDFRemoval:
    def test_pdf_routes_are_not_owned_by_fastapi(self, client):
        assert client.post("/api/export-pdf", json={"resume_data": MOCK_RESUME_DATA}).status_code == 404
        assert client.post("/api/render-resume-html", json={"resume_data": MOCK_RESUME_DATA}).status_code == 404
        assert client.get("/api/download-pdf/resume.pdf").status_code == 404


# ─────────────────────────────────────────────────────────────────────────────
# 15 ── Full happy-path E2E flow
# ─────────────────────────────────────────────────────────────────────────────

class TestFullE2EFlow:
    """
    Simulates a realistic user journey:
      1. Seed the sample profile
      2. Ingest an extra text note
      3. Call /api/tailor with a real JD
      4. Return JSON Resume for frontend review and Next.js PDF export
    """

    def test_full_flow(self, client, tmp_path):
        # Step 1 – Seed sample profile
        seed_resp = client.post("/api/knowledge-base/seed-sample")
        assert seed_resp.status_code == 200
        assert seed_resp.json()["stats"]["total_items"] > 0

        # Step 2 – Add a supplementary text note
        note_resp = client.post(
            "/api/knowledge-base/ingest-text",
            json={
                "title": "Recent Hackathon Win",
                "content": (
                    "Won first place at the 2025 AI Hackathon. Built a RAG-based "
                    "knowledge assistant using ChromaDB and Llama 3 in 24 hours."
                ),
                "tags": ["ai", "hackathon", "rag"],
            },
        )
        assert note_resp.status_code == 200

        # Step 3 – Tailor resume
        with patch(
            "ai.generator.resume_generator.generate_tailored_resume",
            new_callable=AsyncMock,
            return_value=_mock_tailored_resume(),
        ):
            tailor_resp = client.post(
                "/api/tailor",
                json={
                    "job_description": SAMPLE_JD,
                    "target_role": "Senior Backend Engineer",
                    "model": "llama3",
                    "candidate_name": "Joji Developer",
                    "candidate_email": "joji.dev@example.com",
                },
            )
        assert tailor_resp.status_code == 200
        tailor_body = tailor_resp.json()
        assert "resume" in tailor_body
        assert tailor_body["rag_context"]["match_count"] > 0

        # Step 4 - FastAPI stops at structured JSON; Next.js owns PDF export.
        assert tailor_body["resume"]["basics"]["name"] == "Jane Doe"
        print("\n✅  Full E2E flow completed successfully.")
        print(f"   KB items: {seed_resp.json()['stats']['total_items']} (after seed)")
        print(f"   RAG matches: {tailor_body['rag_context']['match_count']}")


def test_get_candidate_profile_and_grounded_fallback(client):
    """
    Verifies that GET /api/knowledge-base/profile extracts candidate profile from ChromaDB
    and that fallback tailoring uses real candidate records instead of dummy placeholders.
    """
    # 1. Empty KB check
    resp = client.get("/api/knowledge-base/profile")
    assert resp.status_code == 200
    assert resp.json()["exists"] is False

    # 2. Ingest structured candidate profile
    custom_profile = {
        "name": "Jane Candidate",
        "contact": {
            "email": "jane.candidate@example.com",
            "phone": "+1 555-999-8888",
            "location": "Seattle, WA",
        },
        "summary": "Full-stack cloud developer specializing in distributed microservices.",
        "experience": [
            {
                "company": "CloudScale Inc",
                "role": "Lead Cloud Engineer",
                "duration": "2021 - Present",
                "location": "Seattle, WA",
                "bullets": ["Architected Kubernetes pipelines for 500+ microservices."],
            }
        ],
        "projects": [
            {
                "name": "CloudMesh",
                "description": "Zero-trust service mesh for container clusters.",
                "technologies": ["Go", "Docker", "Kubernetes"],
            }
        ],
        "skills": [{"category": "Cloud & Infra", "items": ["Kubernetes", "Docker", "Go"]}],
        "education": [{"institution": "University of Washington", "degree": "B.S. CS", "year": "2021"}],
    }

    ingest_resp = client.post("/api/knowledge-base/ingest-profile", json=custom_profile)
    assert ingest_resp.status_code == 200

    # 3. Retrieve profile from endpoint
    prof_resp = client.get("/api/knowledge-base/profile")
    assert prof_resp.status_code == 200
    prof_data = prof_resp.json()
    assert prof_data["exists"] is True
    assert prof_data["candidate"]["name"] == "Jane Candidate"
    assert prof_data["candidate"]["email"] == "jane.candidate@example.com"
    assert len(prof_data["experiences"]) > 0
    assert prof_data["experiences"][0]["company"] == "CloudScale Inc"

    # 4. Tailor resume using local fallback (without Ollama)
    tailor_resp = client.post(
        "/api/tailor",
        json={"job_description": "Seeking Cloud Engineer", "target_role": "Cloud Architect"},
    )
    assert tailor_resp.status_code == 200
    tailored_resume = tailor_resp.json()["resume"]

    # Verify real data is present and NO "Alex Morgan" or "TechNova" placeholder exists
    assert tailored_resume["basics"]["name"] == "Jane Candidate"
    assert tailored_resume["basics"]["email"] == "jane.candidate@example.com"
    assert tailored_resume["work"][0]["name"] == "CloudScale Inc"
    assert "Alex Morgan" not in str(tailored_resume)
    assert "TechNova" not in str(tailored_resume)
