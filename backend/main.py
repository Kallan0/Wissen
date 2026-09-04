import os
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path
from fastapi import FastAPI, HTTPException, Body, Query, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from config import settings
from rag.vectorstore import vector_store
from rag.ingestion import IngestionService
from rag.retriever import rag_retriever
from ai.generator import resume_generator
from pdf.generator import pdf_generator
from connectors import github_connector, canva_connector, creative_fs_connector

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
    template: Optional[str] = "modern"

# --- Health & Models Endpoints ---
@app.get("/api/health")
async def health_check():
    ollama_info = await resume_generator.check_ollama_status()
    db_stats = vector_store.get_stats()
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

@app.post("/api/knowledge-base/ingest-text")
def ingest_text_endpoint(payload: IngestTextRequest):
    chunks = IngestionService.ingest_text(
        content=payload.content,
        title=payload.title,
        category=payload.category,
        tags=payload.tags
    )
    return {"message": f"Successfully ingested {chunks} chunks.", "chunks": chunks}

@app.post("/api/knowledge-base/upload-resume-pdf")
async def upload_resume_pdf(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")
    try:
        content = await file.read()
        chunks = IngestionService.ingest_pdf_file(content, file.filename)
        stats = vector_store.get_stats()
        return {
            "message": f"Successfully parsed and indexed {chunks} chunks from '{file.filename}' into ChromaDB!",
            "chunks": chunks,
            "stats": stats
        }
    except Exception as e:
        logger.error(f"Error parsing uploaded PDF: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/knowledge-base/ingest-profile")
def ingest_profile_endpoint(payload: Dict[str, Any] = Body(...)):
    counts = IngestionService.ingest_structured_profile(payload)
    return {"message": "Profile successfully indexed into ChromaDB", "indexed": counts}

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

    # 1. RAG Retrieval from ChromaDB
    retrieval_output = rag_retriever.retrieve_context_for_jd(payload.job_description)
    
    # 2. Candidate basic info fallback
    cand_info = {
        "name": payload.candidate_name,
        "email": payload.candidate_email,
        "location": payload.candidate_location
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

@app.post("/api/recommend-positions")
async def recommend_positions_endpoint(payload: Optional[RecommendPositionsRequest] = None):
    model_name = payload.model if payload else None

    # Gather verified background from ChromaDB
    all_data = vector_store.get_all_items()
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
        stats = vector_store.get_stats()
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

# --- PDF Export Endpoints ---
@app.post("/api/export-pdf")
async def export_pdf(payload: ExportPDFRequest):
    try:
        pdf_path = await pdf_generator.generate_pdf(
            resume_data=payload.resume_data,
            template_name=payload.template or "modern"
        )
        return {
            "status": "success",
            "filename": pdf_path.name,
            "download_url": f"/api/download-pdf/{pdf_path.name}"
        }
    except Exception as e:
        logger.error(f"Error generating PDF: {e}")
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
