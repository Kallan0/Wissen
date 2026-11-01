# Local AI-Powered Resume Builder

## Overview

The Resume Builder is a privacy-conscious, retrieval-augmented generation (RAG) system that tailors resumes to specific Job Descriptions (JDs). You can run inference locally through Ollama or explicitly select Groq Cloud to avoid using the workstation GPU. The selected model maps verified skills and experience to the JD under strict grounding rules.

## Core Features

- **Online or Offline Inference:** Use local Ollama for device-only processing, or Groq Cloud for GPU-free inference. Cloud mode sends the JD and retrieved verified profile context to Groq.
- **Retrieval-Augmented Generation (RAG):** Preserves logical resume sections and structured records, then uses hybrid ChromaDB retrieval that fuses HNSW ANN dense similarity with BM25 keyword relevance.
- **LLM Query Expansion:** Broad JD concepts such as frontend development are expanded into related frameworks, tools, synonyms, and competencies before retrieval.
- **Resilient Retrieval:** MiniLM is cached inside the writable project data directory; if dense inference is temporarily unavailable, retrieval degrades to BM25 instead of returning an empty context.
- **Strict Hallucination Control:** System prompts are engineered to force the LLM to rely _only_ on the provided context.
- **JSON Resume Contract:** FastAPI returns the official JSON Resume shape so generated data is portable across compatible tools and community themes.
- **Human-in-the-Loop Export:** The frontend exposes every generated section and bullet for review; PDF export stays locked until the user confirms the edited draft.
- **Next.js PDF Generation:** The final reviewed JSON is validated with `@jsonresume/schema` and rendered to A4 by the Next.js server using React PDF.

## Tech Stack

- **Frontend:** Next.js (React), Tailwind CSS
- **Backend:** Python, FastAPI
- **AI / LLM Runners:** Ollama (local/offline) and optional Groq Cloud
- **RAG & Orchestration:** LangChain, ChromaDB (Vector Database), FastEmbed
- **Resume Schema:** JSON Resume (`@jsonresume/schema`)
- **PDF Rendering:** Next.js route with `@react-pdf/renderer`

---

## System Architecture

1. **Data Ingestion (The Knowledge Base):**
   Scripts pull data from PDFs, text, GitHub repos, local markdown files, and portfolio metadata. Resume headings, Markdown sections, work records, projects, education entries, and skill groups remain logical units. Unstructured prose uses semantic sentence boundaries rather than character windows.
2. **User Input:**
   User pastes a Job Description into the Next.js web interface.
3. **Query Expansion and Retrieval:**
   The selected LLM expands broad JD concepts into adjacent technologies and synonyms. FastAPI appends those concepts to the search query and combines Chroma's cosine HNSW approximate-nearest-neighbour results with BM25 lexical scores. The default fused relevance is 70% dense and 30% BM25, with a permissive `HYBRID_MIN_SCORE=0.0` for fuzzy matches.
4. **Generation:**
   The backend constructs a prompt combining the JD, retrieved context, and strict system rules, then calls the user-selected Ollama or Groq model.
5. **Schema Conversion:**
   A deterministic backend adapter converts the grounded draft to JSON Resume (`basics`, `work`, `projects`, `skills`, `education`, and namespaced `custom` metadata).
6. **Human Review:**
   The Next.js UI displays an editable form for identity, summaries, work entries, projects, skills, education, and every generated highlight. Export remains disabled until the user confirms review.
7. **Formatting & Export:**
   The edited JSON is posted only to the Next.js `/api/export-pdf` route, validated against the official schema, and rendered with React PDF. FastAPI never generates or stores the PDF.

---

## Installation & Setup

### Prerequisites

- [Node.js](https://nodejs.org/) (v18+)
- [Python 3.10+](https://www.python.org/)
- [Ollama](https://ollama.ai/) installed and running locally.

### 1. Model Setup

Download and run your preferred local model:

```bash
ollama run llama3
```

### Recommended: start the complete local stack

From the repository root:

```powershell
npm install
npm run dev:check
npm run dev
```

The startup preflight checks ports `3000`, `8001`, and `11434`. Healthy Wissen frontend/backend instances and an existing Ollama server are reused; an unrelated listener fails before any child services are launched. This prevents one port collision from starting and then terminating the rest of the stack.

On the first semantic search, Chroma downloads the MiniLM ONNX model (about 79 MB) into `backend/data/embedding_cache`. To warm it before startup, run:

```powershell
backend\venv\Scripts\python.exe scripts\warm_embedding_cache.py
```

If preflight reports an unknown listener on Windows, inspect it before stopping it:

```powershell
Get-NetTCPConnection -LocalPort 3000 -State Listen | Select-Object OwningProcess
Get-CimInstance Win32_Process -Filter "ProcessId=<PID>" | Select-Object Name, CommandLine
```

Ollama warnings about its online recommendations endpoint are non-fatal when local `/api/version` and `/api/tags` requests still succeed.

### Optional: Groq Cloud inference

Create a key in the [Groq Console](https://console.groq.com/keys), then copy the example configuration and place the key only in the ignored root `.env` file. The integration uses Groq's official [OpenAI-compatible Chat Completions API](https://console.groq.com/docs/openai).

```powershell
Copy-Item .env.example .env
```

Edit `.env`:

```dotenv
GROQ_API_KEY=your_key_from_groq_console
GROQ_DEFAULT_MODEL=openai/gpt-oss-20b
GROQ_MODELS=openai/gpt-oss-20b
AI_DEFAULT_PROVIDER=groq
OLLAMA_ENABLED=false
```

Restart the app after changing `.env`. With `OLLAMA_ENABLED=false`, the root launcher does not start Ollama and the selector offers Groq only, avoiding local model GPU use. Set it to `true` whenever you want both Groq Cloud and Ollama Local choices. The API key remains on the backend and is never returned to the browser. Selecting Groq transmits the target JD plus the retrieved verified candidate context to Groq; select Ollama when that data must remain on the device.

### 2. Backend Setup (FastAPI & RAG)

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`

# Install the tested runtime dependencies
pip install -r requirements.txt

# Run the API server
uvicorn main:app --reload --port 8001
```

### 3. Frontend Setup (Next.js)

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Run the development server
npm run dev
```

---

## Data Ingestion & Integrations

Populate the local knowledge base through the web UI or the existing connectors:

- **Resume PDF:** Upload a resume and extract its text locally.
- **GitHub:** Pull repository descriptions, language statistics, topics, and README summaries.
- **Canva / UI/UX:** Add structured design-project evidence.
- **Local projects and note vaults:** Scan selected Unity, Blender, code, Markdown, or text directories.

### Example Ingestion Script

```python
from rag.ingestion import IngestionService

raw_text = "I am a full-stack developer with experience in Next.js, Python, and UI/UX design..."
chunks_added = IngestionService.ingest_text(
    content=raw_text,
    title="Professional profile",
    tags=["profile"],
)
print(f"Indexed {chunks_added} chunks")
```

## Future Roadmap

- [ ] Implement iterative refinement (letting the LLM critique its own generated resume against the JD before finalizing).
- [ ] Add authenticated access before exposing the backend beyond localhost.
- [ ] Complete evaluated adapter merge, GGUF conversion, and rollback automation.
