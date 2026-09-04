# Local AI-Powered Resume Builder

## Overview
The Local AI Resume Builder is a privacy-first, retrieval-augmented generation (RAG) system designed to automatically tailor resumes to specific Job Descriptions (JDs). By keeping all personal data and LLM processing local, the system guarantees 100% data privacy. The model acts strictly as an orchestrator, mapping your existing skills and experiences to the target JD without hallucinating fabricated qualifications.

## Core Features
- **Privacy-First (Local LLMs):** Powered by local models (e.g., Llama 3, Mistral) via Ollama. No personal data is sent to external APIs (like OpenAI).
- **Retrieval-Augmented Generation (RAG):** Uses a local vector database (ChromaDB) to retrieve only the most relevant projects, work experiences, and skills based on the input Job Description.
- **Strict Hallucination Control:** System prompts are engineered to force the LLM to rely *only* on the provided context.
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
   FastAPI receives the JD, embeds it, and queries ChromaDB for the top *K* most relevant experiences and skills.
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

### 2. Backend Setup (FastAPI & RAG)
```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`

# Install dependencies
pip install fastapi uvicorn langchain langchain-community chromadb fastembed pydantic

# Run the API server
uvicorn main:app --reload --port 8000
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

To populate your RAG database, you will create modular Python scripts to parse various data sources:

- **GitHub:** Use `PyGithub` to pull READMEs, repository descriptions, and language statistics.
- **Canva / UI/UX:** Export design metadata or project briefs to JSON/Markdown and embed.
- **Unity / Blender:** Write local filesystem parsers to read project directory structures, `.meta` files, or custom `project_summary.txt` files inside your workflow directories.

### Example Ingestion Script
```python
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import FastEmbedEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter

# Load your personal data documents here
raw_text = "I am a full-stack developer with experience in Next.js, Python, and UI/UX design..."

text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
chunks = text_splitter.split_text(raw_text)

db = Chroma.from_texts(
    texts=chunks, 
    embedding=FastEmbedEmbeddings(), 
    persist_directory="./chroma_db"
)
print("Data ingested successfully!")
```

## Future Roadmap
- [ ] Add PDF parsing to automatically ingest old versions of your resume.
- [ ] Build a template selector in the Next.js frontend.
- [ ] Implement iterative refinement (letting the LLM critique its own generated resume against the JD before finalizing).
