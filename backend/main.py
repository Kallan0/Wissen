import os
import sys
import asyncio
import logging
from typing import Dict, Any, List, Literal, Optional
from pathlib import Path

# ── Windows asyncio fix ───────────────────────────────────────────────────────
# The default SelectorEventLoop on Windows cannot spawn subprocesses, which
# Playwright needs to launch Chromium.  ProactorEventLoop supports both I/O
# and subprocess creation, making it the correct choice for Windows.
if sys.platform == "win32" and sys.version_info < (3, 14):
    set_policy = getattr(asyncio, "set_event_loop_policy", None)
    proactor_policy = getattr(asyncio, "WindowsProactorEventLoopPolicy", None)
    if set_policy and proactor_policy:
        try:
            set_policy(proactor_policy())
        except Exception:
            pass
# ─────────────────────────────────────────────────────────────────────────────

from fastapi import FastAPI, HTTPException, Body, Query, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel, Field

from config import settings
from rag.vectorstore import vector_store
from rag.ingestion import IngestionService
from rag.profile_normalization import normalize_profile_submission
from rag.retriever import rag_retriever
from ai.generator import resume_generator
from pdf.generator import pdf_generator
from connectors import github_connector, canva_connector, creative_fs_connector
from connectors.linkedin_connector import linkedin_connector
from connectors.vault_connector import vault_connector

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("resume_builder.main")

app = FastAPI(
    title="Local AI Resume Builder API",
    description="Privacy-First, Retrieval-Augmented Generation (RAG) Resume Customizer",
    version="1.0.0"
)

# Enable CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Pydantic Schemas ---
class IngestTextRequest(BaseModel):
    title: str = Field(..., description="Title of the text/markdown note")
    content: str = Field(..., description="Markdown or plain text content")
    category: Optional[str] = "raw_documents"
    tags: Optional[List[str]] = []

class TailorResumeRequest(BaseModel):
    job_description: str = Field(..., description="The target Job Description text")
    target_role: Optional[str] = Field("Software Engineer", description="Target job title")
    model: Optional[str] = Field("llama3", description="Ollama model name")
    candidate_name: Optional[str] = None
    candidate_email: Optional[str] = None
    candidate_location: Optional[str] = None
    template: Optional[str] = "modern"

class RecommendPositionsRequest(BaseModel):
    model: Optional[str] = Field("llama3", description="Ollama model name")

class GitHubSyncRequest(BaseModel):
    username: str = Field(..., description="GitHub username")
    token: Optional[str] = Field(None, description="Optional GitHub Personal Access Token")
    max_repos: Optional[int] = Field(15, description="Maximum repos to fetch")
    fetch_readme: Optional[bool] = Field(True, description="Whether to parse READMEs")

class CanvaProjectRequest(BaseModel):
    title: str = Field(..., description="Project Title")
    description: str = Field(..., description="Design Overview")
    design_type: Optional[str] = Field("UI/UX & Visual Design", description="Type of design")
    tools_used: Optional[List[str]] = Field(["Canva", "Figma"], description="Tools used")
    prototype_url: Optional[str] = Field(None, description="Prototype or presentation link")
    deliverables: Optional[List[str]] = Field([], description="Deliverables")
    user_impact: Optional[str] = Field(None, description="Impact or user metrics")

class FilesystemScanRequest(BaseModel):
    directory_path: str = Field(..., description="Local folder path (e.g. Unity or Blender project)")
    custom_project_name: Optional[str] = Field(None, description="Optional custom name for the project")

class ExportPDFRequest(BaseModel):
    resume_data: Dict[str, Any] = Field(..., description="Structured resume JSON")
    template: Literal["modern", "minimal", "vintage"] = "modern"

class LinkedInSyncRequest(BaseModel):
    positions_csv: Optional[str] = Field(None, description="Raw Positions.csv content")
    skills_csv: Optional[str] = Field(None, description="Raw Skills.csv content")

class VaultScanRequest(BaseModel):
    directory_path: str = Field(..., description="Local Obsidian or Notion markdown folder path")
    category: Optional[str] = "markdown_vault"

class CoverLetterRequest(BaseModel):
    job_description: str = Field(..., description="Target Job Description text")
    target_role: Optional[str] = Field("Software Engineer", description="Target job title")
    model: Optional[str] = Field("llama3", description="Ollama model name")

class ATSAnalysisRequest(BaseModel):
    job_description: str = Field(..., description="Target Job Description text")
    model: Optional[str] = Field("llama3", description="Ollama model name")


def normalize_resume_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Ensure all required fields exist with safe defaults before PDF rendering."""
    contact = data.get("contact") or {}
    if not isinstance(contact, dict):
        contact = {}
    return {
        "name": data.get("name") or "Candidate",
        "title": data.get("title") or data.get("target_role") or "Professional",
        "contact": {
            "email": contact.get("email") or "",
            "phone": contact.get("phone") or "",
            "location": contact.get("location") or "",
            "linkedin": contact.get("linkedin") or "",
            "github": contact.get("github") or "",
            "portfolio": contact.get("portfolio") or "",
        },
        "summary": data.get("summary") or "",
        "skills": [
            {
                "category": s.get("category", "Skills") if isinstance(s, dict) else "Skills",
                "items": s.get("items", []) if isinstance(s, dict) else []
            }
            for s in (data.get("skills") or [])
        ],
        "experience": [
            {
                "company": e.get("company", "") if isinstance(e, dict) else "",
                "role": e.get("role", "") if isinstance(e, dict) else "",
                "duration": e.get("duration", "") if isinstance(e, dict) else "",
                "location": e.get("location", "") if isinstance(e, dict) else "",
                "bullets": e.get("bullets") or e.get("highlights") or [] if isinstance(e, dict) else [],
                "technologies": e.get("technologies") or [] if isinstance(e, dict) else [],
            }
            for e in (data.get("experience") or [])
        ],
        "projects": [
            {
                "name": p.get("name", "") if isinstance(p, dict) else "",
                "description": p.get("description", "") if isinstance(p, dict) else "",
                "technologies": p.get("technologies") or [] if isinstance(p, dict) else [],
                "bullets": p.get("bullets") or p.get("highlights") or [] if isinstance(p, dict) else [],
                "highlights": p.get("highlights") or p.get("bullets") or [] if isinstance(p, dict) else [],
                "link": p.get("link", "") if isinstance(p, dict) else "",
            }
            for p in (data.get("projects") or [])
        ],
        "education": [
            {
                "institution": e.get("institution", "") if isinstance(e, dict) else "",
                "degree": e.get("degree", "") if isinstance(e, dict) else "",
                "year": e.get("year", "") if isinstance(e, dict) else "",
                "details": e.get("details", "") if isinstance(e, dict) else "",
            }
            for e in (data.get("education") or [])
        ],
    }

# --- Health & Models Endpoints ---
@app.get("/api/health")
async def health_check():
    ollama_info, db_stats = await asyncio.gather(
        resume_generator.check_ollama_status(),
        asyncio.to_thread(vector_store.get_stats),
    )
    return {
        "status": "healthy",
        "ollama": ollama_info,
        "knowledge_base": db_stats
    }

@app.get("/api/models")
async def get_models():
    models = await resume_generator.get_available_models()
    return {"models": models}

# --- Knowledge Base Endpoints ---
@app.get("/api/knowledge-base/stats")
def get_kb_stats():
    return vector_store.get_stats()

@app.get("/api/knowledge-base/items")
def get_kb_items():
    return vector_store.get_all_items()

@app.get("/api/knowledge-base/profile")
def get_kb_profile():
    return vector_store.get_candidate_profile()

@app.post("/api/knowledge-base/ingest-text")
def ingest_text_endpoint(payload: IngestTextRequest):
    chunks = IngestionService.ingest_text(
        content=payload.content,
        title=payload.title,
        category=payload.category or "raw_documents",
        tags=payload.tags
    )
    return {"message": f"Successfully ingested {chunks} chunks.", "chunks": chunks}

@app.post("/api/knowledge-base/upload-resume-pdf")
async def upload_resume_pdf(file: UploadFile = File(...)):
    filename = file.filename or "uploaded_resume.pdf"
    if not filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")
    try:
        content = await file.read()
        chunks = IngestionService.ingest_pdf_file(content, filename)
        stats = vector_store.get_stats()
        return {
            "message": f"Successfully parsed and indexed {chunks} chunks from '{filename}' into ChromaDB!",
            "chunks": chunks,
            "stats": stats
        }
    except Exception as e:
        logger.error(f"Error parsing uploaded PDF: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/knowledge-base/ingest-profile")
def ingest_profile_endpoint(payload: Dict[str, Any] = Body(...)):
    try:
        normalized_profile = normalize_profile_submission(payload)
        counts = IngestionService.ingest_structured_profile(normalized_profile)
        return {"message": "Profile successfully indexed into ChromaDB", "indexed": counts}
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))

@app.post("/api/knowledge-base/seed-sample")
def seed_sample_endpoint():
    sample_file = settings.SAMPLE_DIR / "sample_profile.json"
    if not sample_file.exists():
        raise HTTPException(status_code=404, detail="Sample profile file not found.")
    
    import json
    with open(sample_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    vector_store.clear_all()
    counts = IngestionService.ingest_structured_profile(data)
    stats = vector_store.get_stats()
    return {"message": "Knowledge base seeded with rich sample profile.", "counts": counts, "stats": stats}

@app.post("/api/knowledge-base/clear")
def clear_kb_endpoint():
    vector_store.clear_all()
    return {"message": "Knowledge base reset."}

# --- RAG Retrieval & Tailoring Endpoints ---
@app.post("/api/tailor")
async def tailor_resume(payload: TailorResumeRequest):
    if not payload.job_description.strip():
        raise HTTPException(status_code=400, detail="Job description cannot be empty.")

    # Check if Knowledge Base has any items
    db_profile = await asyncio.to_thread(vector_store.get_candidate_profile)
    if not db_profile.get("exists"):
        raise HTTPException(
            status_code=400,
            detail="Your Knowledge Base is empty! Please upload a PDF resume or complete the profile questionnaire before tailoring."
        )

    try:
        # 1. RAG Retrieval from ChromaDB
        retrieval_output = await asyncio.to_thread(
            rag_retriever.retrieve_context_for_jd,
            payload.job_description,
        )

        # 2. Candidate basic info resolution (Explicit payload > ChromaDB stored identity)
        c_meta = db_profile.get("candidate", {})
        cand_info = {
            "name": payload.candidate_name or c_meta.get("name") or "",
            "email": payload.candidate_email or c_meta.get("email") or "",
            "location": payload.candidate_location or c_meta.get("location") or "",
            "linkedin": c_meta.get("linkedin") or "",
            "github": c_meta.get("github") or "",
            "portfolio": c_meta.get("portfolio") or ""
        }

        # 3. LLM Orchestration via Ollama (with resilient fallback)
        tailored_resume = await resume_generator.generate_tailored_resume(
            job_description=payload.job_description,
            retrieved_context=retrieval_output["formatted_context"],
            target_role=payload.target_role or "Software Engineer",
            candidate_info=cand_info,
            model=payload.model
        )

        return {
            "resume": tailored_resume,
            "rag_context": {
                "match_count": retrieval_output["match_count"],
                "retrieved_items": retrieval_output["retrieved_items"],
                "keywords": retrieval_output["extracted_keywords"]
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Unexpected error in /api/tailor: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Resume tailoring failed: {str(e)}")

@app.post("/api/recommend-positions")
async def recommend_positions_endpoint(payload: Optional[RecommendPositionsRequest] = None):
    model_name = payload.model if payload else None

    # Gather verified background from ChromaDB
    all_data = await asyncio.to_thread(vector_store.get_all_items)
    context_lines = []

    for category in ["experiences", "projects", "skills", "education", "raw_documents"]:
        items = all_data.get(category, [])
        if items:
            context_lines.append(f"=== VERIFIED {category.upper()} ===")
            for item in items:
                context_lines.append(f"- {item['document']}")
            context_lines.append("")

    if not context_lines:
        raise HTTPException(
            status_code=400,
            detail="Knowledge base is empty. Please add experiences, projects, or notes to ChromaDB first."
        )

    full_context = "\n".join(context_lines)
    recommendations = await resume_generator.suggest_career_positions(
        candidate_context=full_context,
        model=model_name
    )
    return recommendations

# --- Data Connectors Endpoints ---
@app.post("/api/connectors/github/sync")
async def sync_github_endpoint(payload: GitHubSyncRequest):
    try:
        result = await github_connector.sync_user_repositories(
            username=payload.username,
            token=payload.token,
            max_repos=payload.max_repos or 15,
            fetch_readme=payload.fetch_readme if payload.fetch_readme is not None else True
        )
        stats = await asyncio.to_thread(vector_store.get_stats)
        return {"status": "success", "result": result, "stats": stats}
    except Exception as e:
        logger.error(f"GitHub sync error: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/connectors/canva/sync")
def sync_canva_endpoint(payload: CanvaProjectRequest):
    try:
        result = canva_connector.ingest_design_project(
            title=payload.title,
            description=payload.description,
            design_type=payload.design_type or "UI/UX & Visual Design",
            tools_used=payload.tools_used,
            prototype_url=payload.prototype_url,
            deliverables=payload.deliverables,
            user_impact=payload.user_impact
        )
        stats = vector_store.get_stats()
        return {"status": "success", "result": result, "stats": stats}
    except Exception as e:
        logger.error(f"Canva sync error: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/connectors/filesystem/scan")
def scan_filesystem_endpoint(payload: FilesystemScanRequest):
    try:
        result = creative_fs_connector.scan_and_ingest_directory(
            directory_path=payload.directory_path,
            custom_project_name=payload.custom_project_name
        )
        stats = vector_store.get_stats()
        return {"status": "success", "result": result, "stats": stats}
    except Exception as e:
        logger.error(f"Filesystem scan error: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/connectors/linkedin/parse-csv")
def parse_linkedin_csv_endpoint(payload: LinkedInSyncRequest):
    try:
        result = linkedin_connector.ingest_linkedin_archive({
            "positions": payload.positions_csv or "",
            "skills": payload.skills_csv or ""
        })
        return result
    except Exception as e:
        logger.error(f"LinkedIn CSV parse error: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/connectors/vault/scan")
def scan_vault_endpoint(payload: VaultScanRequest):
    try:
        result = vault_connector.scan_and_ingest_vault(
            directory_path=payload.directory_path,
            category=payload.category or "markdown_vault"
        )
        return result
    except Exception as e:
        logger.error(f"Markdown Vault scan error: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/generate-cover-letter")
async def generate_cover_letter_endpoint(payload: CoverLetterRequest):
    if not payload.job_description.strip():
        raise HTTPException(status_code=400, detail="Job description cannot be empty.")
    try:
        result = await resume_generator.generate_cover_letter(
            job_description=payload.job_description,
            target_role=payload.target_role or "Software Engineer",
            model=payload.model
        )
        return result
    except Exception as e:
        logger.error(f"Cover letter generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/analyze-ats-gap")
async def analyze_ats_gap_endpoint(payload: ATSAnalysisRequest):
    if not payload.job_description.strip():
        raise HTTPException(status_code=400, detail="Job description cannot be empty.")
    try:
        result = await resume_generator.analyze_ats_gap(
            job_description=payload.job_description,
            model=payload.model
        )
        return result
    except Exception as e:
        logger.error(f"ATS gap analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# --- PDF Export Endpoints ---
@app.post("/api/render-resume-html", response_class=HTMLResponse)
async def render_resume_html(payload: ExportPDFRequest):
    """Render the same backend-owned template used for PDF export."""
    try:
        clean_data = normalize_resume_data(payload.resume_data)
        return HTMLResponse(
            content=pdf_generator.render_html(
                resume_data=clean_data,
                template_name=payload.template or "modern",
            )
        )
    except Exception as e:
        logger.error(f"Error rendering resume preview: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Resume preview failed: {str(e)}")


@app.post("/api/export-pdf")
async def export_pdf(payload: ExportPDFRequest):
    try:
        clean_data = normalize_resume_data(payload.resume_data)
        pdf_path = await pdf_generator.generate_pdf(
            resume_data=clean_data,
            template_name=payload.template or "modern"
        )
        return {
            "status": "success",
            "filename": pdf_path.name,
            "download_url": f"/api/download-pdf/{pdf_path.name}"
        }
    except Exception as e:
        logger.error(f"Error generating PDF: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {str(e)}")

@app.get("/api/download-pdf/{filename}")
async def download_pdf(filename: str):
    file_path = settings.PDF_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Requested PDF file not found.")
    return FileResponse(
        path=str(file_path),
        filename=filename,
        media_type="application/pdf"
    )

# --- Fine-Tuning & Custom Models Endpoints ---
class ExportDatasetRequest(BaseModel):
    count: int = Field(default=150, ge=100, le=200)
    model: Optional[str] = Field(None, description="Installed Ollama model used to generate reviewed examples")

@app.post("/api/finetuning/export-dataset")
async def export_finetuning_dataset(payload: ExportDatasetRequest = ExportDatasetRequest()):
    try:
        from finetuning.dataset_generator import build_dataset
        from finetuning.split_dataset import split_dataset
        dataset_dir = settings.DATA_DIR / "finetuning"
        dataset_dir.mkdir(parents=True, exist_ok=True)
        generated_file = dataset_dir / "generated_dataset.jsonl"
        training_file = dataset_dir / "training_data.jsonl"
        holdout_file = dataset_dir / "holdout_eval.jsonl"

        file_path_str = await asyncio.to_thread(
            build_dataset,
            payload.count,
            str(generated_file),
            payload.model,
        )
        training_count, holdout_count = await asyncio.to_thread(
            split_dataset,
            Path(file_path_str),
            training_file,
            holdout_file,
            seed=42,
            train_ratio=0.8,
        )
        file_size = os.path.getsize(training_file)

        return {
            "status": "success",
            "count": training_count,
            "generated_count": payload.count,
            "holdout_count": holdout_count,
            "filename": "training_data.jsonl",
            "file_size_bytes": file_size,
            "download_url": "/api/finetuning/download-dataset/training_data.jsonl",
            "holdout_filename": "holdout_eval.jsonl",
            "holdout_download_url": "/api/finetuning/download-dataset/holdout_eval.jsonl",
        }
    except Exception as e:
        logger.error(f"Error generating fine-tuning dataset: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Dataset generation failed: {str(e)}")

@app.get("/api/finetuning/download-dataset/{filename}")
async def download_finetuning_dataset(filename: str):
    file_path = settings.DATA_DIR / "finetuning" / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Dataset file not found. Please generate it first.")
    return FileResponse(
        path=str(file_path),
        filename=filename,
        media_type="application/jsonl"
    )

@app.get("/api/finetuning/status")
async def get_finetuning_status():
    try:
        models = await resume_generator.get_available_models()
        custom_models = [m for m in models if "resume" in m.lower() or "custom" in m.lower() or "tailor" in m.lower()]
        base_models = [m for m in models if m not in custom_models]

        colab_nb_exists = (settings.BASE_DIR / "finetuning" / "fine_tune_colab.ipynb").exists()
        modelfile_exists = (settings.BASE_DIR / "finetuning" / "Modelfile").exists()

        return {
            "installed_models": models,
            "custom_models": custom_models,
            "base_models": base_models,
            "has_custom_model_active": len(custom_models) > 0,
            "toolkit": {
                "modelfile_available": modelfile_exists,
                "colab_notebook_available": colab_nb_exists
            }
        }
    except Exception as e:
        logger.error(f"Error fetching fine-tuning status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Fine-tuning status check failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)

