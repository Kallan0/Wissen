# Local AI-Powered Resume Builder

## Overview

The Local AI Resume Builder is a privacy-first, retrieval-augmented generation (RAG) system designed to automatically tailor resumes to specific Job Descriptions (JDs). By keeping all personal data and LLM processing local, the system guarantees 100% data privacy. The model acts strictly as an orchestrator, mapping your existing skills and experiences to the target JD without hallucinating fabricated qualifications.

## Core Features

- **Privacy-First (Local LLMs):** Powered by local models (e.g., Llama 3, Mistral) via Ollama. No personal data is sent to external APIs (like OpenAI).
- **Retrieval-Augmented Generation (RAG):** Uses a local vector database (ChromaDB) to retrieve only the most relevant projects, work experiences, and skills based on the input Job Description.
- **Strict Hallucination Control:** System prompts are engineered to force the LLM to rely _only_ on the provided context.
- **PDF Generation:** Automated conversion of generated HTML/React templates into pixel-perfect PDF resumes.

## Tech Stack

- **Frontend:** Next.js (React), Tailwind CSS
- **Backend:** Python, FastAPI
- **AI / LLM Runner:** Ollama (Local LLM Execution)
- **RAG & Orchestration:** LangChain, ChromaDB (Vector Database), FastEmbed
- **PDF Rendering:** Puppeteer / Playwright (Headless Browser PDF generation)

---

## System Architecture

1. **Data Ingestion (The Knowledge Base):**
   Scripts pull data from GitHub repos, local markdown files, portfolio descriptions, and software metadata (e.g., Unity/Blender project summaries) and embed them into ChromaDB.
2. **User Input:**
   User pastes a Job Description into the Next.js web interface.
3. **Retrieval:**
   FastAPI receives the JD, embeds it, and queries ChromaDB for the top _K_ most relevant experiences and skills.
4. **Generation:**
   LangChain constructs a prompt combining the JD, the retrieved context, and strict system rules, then queries the local Ollama model.
5. **Formatting & Export:**
   The parsed LLM response is injected into an HTML template. A headless browser renders this HTML and prints it to a PDF, returning the download link to the frontend.

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

If preflight reports an unknown listener on Windows, inspect it before stopping it:

```powershell
Get-NetTCPConnection -LocalPort 3000 -State Listen | Select-Object OwningProcess
Get-CimInstance Win32_Process -Filter "ProcessId=<PID>" | Select-Object Name, CommandLine
```

Ollama warnings about its online recommendations endpoint are non-fatal when local `/api/version` and `/api/tags` requests still succeed.

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
