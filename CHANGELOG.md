# Changelog & Version History

All notable changes, architectural decisions, and version milestones for the **Local AI-Powered Resume Builder** are documented in this file. Detailed version logs can be found in the [`versions/`](file:///c:/Users/Joji/2026%20Exp/Resume_builder/versions/) directory.

## [v1.20.0] - 2026-09-24

### Summary

Validated the Colab LoRA adapter and added a resumable T4 holdout-inference notebook plus a local factual/schema/leakage scorer, keeping merge and Ollama export blocked until all 30 untouched holdout records pass automated and manual review. See [`versions/v1.20.0.md`](versions/v1.20.0.md).

---

## [v1.19.0] - 2026-09-24

### Summary

Fixed the cascading development startup failure caused by stale port listeners: startup now preflights ports 3000/8001/11434, reuses healthy Wissen and Ollama services, rejects unknown conflicts before launching children, and starts only missing services. See [`versions/v1.19.0.md`](versions/v1.19.0.md).

---

## [v1.18.0] - 2026-09-24

### Summary

Added the persistent `Night Press` dark theme with system-preference initialization, no-flash hydration, theme-aware editorial color and shadow tokens, and a responsive header toggle while preserving the résumé preview as a white print document. See [`versions/v1.18.0.md`](versions/v1.18.0.md).

---

## [v1.17.0] - 2026-09-24

### Summary

Made the backend the single owner of resume HTML/PDF templates and profile normalization, removed three duplicate frontend renderers and synthetic candidate fallbacks, enabled template auto-escaping, and documented the remaining frontend/backend boundary decisions. See [`FRONTEND_BACKEND_BOUNDARY_AUDIT.md`](FRONTEND_BACKEND_BOUNDARY_AUDIT.md) and [`versions/v1.17.0.md`](versions/v1.17.0.md).

---

## [v1.16.0] - 2026-09-24

### Summary

Fixed the Colab QLoRA first-step BF16/FP16 AMP failure by selecting compute precision from the GPU and promoting trainable LoRA weights to FP32 before training; added notebook regression coverage and the same safety guard to the local trainer. See [`versions/v1.16.0.md`](versions/v1.16.0.md).

---

## [v1.15.0] - 2026-09-22

### Summary

Verified gated Llama 3 access, cached the complete 8B checkpoint, detected the local 6 GB VRAM limit before training, and replaced the outdated Colab notebook with a current T4 QLoRA workflow featuring exact-dataset validation, Drive checkpoint resume, secure Hugging Face login, and evaluation-gated adapter export. See [`versions/v1.15.0.md`](versions/v1.15.0.md).

---

## [v1.14.0] - 2026-09-22

### Summary

Reduced backend cold-import time to about 0.8 seconds through lazy ChromaDB, Playwright, and PDF-parser loading; moved blocking database work off async request handlers; isolated E2E storage; removed the superseded QLoRA trainer and unused runtime dependencies; and cleaned regenerable build/cache artifacts. See [`versions/v1.14.0.md`](versions/v1.14.0.md).

---

## [v1.13.0] - 2026-09-22

### Summary

Added fail-fast Hugging Face gated-model authorization checks to training and preflight, documented secure environment-scoped login, and replaced the prior long download traceback with actionable recovery guidance. See [`versions/v1.13.0.md`](versions/v1.13.0.md).

---

## [v1.12.0] - 2026-09-21

### Summary

Fixed evaluation failure accounting, diagnosed the 30-request baseline as invalid because Ollama was offline, and added QLoRA preflight checks for dataset isolation, hashes, dependencies, CUDA, disk space, and artifact paths. See [`versions/v1.12.0.md`](versions/v1.12.0.md).

---

## [v1.11.0] - 2026-09-21

### Summary

Recorded 30/30 manual dataset acceptances and implemented the untouched-holdout Ollama evaluation harness with reproducible settings, raw-output capture, latency measurement, schema scoring, and factual/static-profile checks. See [`versions/v1.11.0.md`](versions/v1.11.0.md).

---

## [v1.10.0] - 2026-09-21

### Summary

Completed Phase 1 dataset-audit automation with static profile checks, leakage detection, unsupported-number warnings, duplicate analysis, machine-readable reports, and a balanced 30-record manual-review packet. The current dataset has zero hard errors and awaits manual factual approval. See [`versions/v1.10.0.md`](versions/v1.10.0.md).

---

## [v1.9.0] - 2026-09-21

### Summary

Added a phased fine-tuning implementation plan with explicit Codex/manual ownership, factual-safety gates, baseline and holdout evaluation requirements, training/export steps, application integration work, and rollback controls. See [`backend/finetuning/NEXT_STEPS_PLAN.md`](backend/finetuning/NEXT_STEPS_PLAN.md) and [`versions/v1.9.0.md`](versions/v1.9.0.md).

---

## [v1.8.0] - 2026-09-21

### Summary

Made candidate identity and static resume metadata deterministic in Python, deduplicated prompt context, added bounded local parallel generation, and successfully produced 150 validated examples split into 120 training and 30 zero-overlap holdout records. See [`versions/v1.8.0.md`](versions/v1.8.0.md).

---

## [v1.7.0] - 2026-09-21

### Summary

Overhauled dataset generation to remove synthetic-persona fallbacks, require verified name/experience/skills, generate grounded variations for backend, frontend, and UI/UX roles through Ollama, and create deterministic 80/20 training and holdout datasets. The attempted 150-record run safely stopped because the live profile lacks a verified name and experience. See [`versions/v1.7.0.md`](versions/v1.7.0.md).

---

## [v1.6.0] - 2026-09-21

### Summary

Completed a repository-wide technical audit and added a validated Llama 3 QLoRA implementation with dataset schema checks, placeholder rejection, deduplication, deterministic evaluation splitting, isolated training dependencies, reproducibility manifests, and unit coverage. See [`versions/v1.6.0.md`](versions/v1.6.0.md) and [`AUDIT.md`](AUDIT.md).

---

## [v1.5.0] - 2026-09-04

### Summary

Replaced navigation layout to match the Google Stitch screen architecture: top header contains strictly the official Stitch MCP logo, the name "Wissen", and a "Login" button; all navigation links and system telemetry have been transitioned to the fixed right-hand sidebar panel (`w-72`) with Artisan Desk profile docket, vertical buttons (`[01]` through `[05]`), and draft entry action. Detailed report in [`versions/v1.5.0.md`](file:///c:/Users/Joji/2026%20Exp/Resume_builder/versions/v1.5.0.md).

---

## [v1.4.0] - 2026-09-04

### Summary

Adapted the tactile editorial papercraft design system from Google Stitch project `projects/15408599458364454127` ("Wissen — Tactile Typewriter Resume Press"). Re-themed the entire frontend interface and headless Playwright PDF export engine with Google Fonts (`Newsreader`, `Source Serif 4`, `Courier Prime`), warm paper/manila palettes, typewriter key navigation, postal cancellation stamps, and mechanical press buttons, while retaining 100% of the underlying RAG vector database, Ollama synthesis, and connector functionalities. Detailed report in [`versions/v1.4.0.md`](file:///c:/Users/Joji/2026%20Exp/Resume_builder/versions/v1.4.0.md).

---

## [v1.3.0] - 2026-09-04

### Summary

Added the **Multi-Source Data Connectors Hub** featuring automated ingestion for **GitHub** (repositories, language statistics, and README summaries), **Canva / UI-UX Design** (case studies, tools, prototypes, and impact metrics), and **Local Game Engine Workspaces** (scanning Unity, Blender, and code directories). Detailed report in [`versions/v1.3.0.md`](file:///c:/Users/Joji/2026%20Exp/Resume_builder/versions/v1.3.0.md).

---

## [v1.2.0] - 2026-09-04

### Summary

Removed all initial sample data from ChromaDB (leaving vector database completely clean at 0 records) and added direct **Resume PDF Upload & Parsing** using `pypdf`, allowing users to import their real resume in 1 click. Detailed report in [`versions/v1.2.0.md`](file:///c:/Users/Joji/2026%20Exp/Resume_builder/versions/v1.2.0.md).

---

## [v1.1.0] - 2026-09-04

### Summary

Added an AI-driven Career Position Recommender ("Role Matches") that analyzes the candidate's verified ChromaDB vector database to recommend target roles with fit scores and proof points. Enhanced Ollama model auto-detection and connected one-click role tailoring.

### Changes Made & Rationale

#### 1. AI Position Recommender Engine (`backend/ai/prompts.py`, `backend/ai/generator.py`)

- **Changes**:
  - Added `ROLE_RECOMMENDATION_PROMPT` with strict anti-hallucination rules to evaluate candidate credentials directly from the vector store.
  - Implemented `suggest_career_positions()` in `ResumeGenerator` to query local Ollama models or synthesize structured career positions.
  - Added smart model fallback that automatically detects installed models (e.g. `gemma4:31b-cloud`) without failing on missing default model names.
- **Reason**:
  - The user requested an AI feature that identifies which positions they are qualified to apply for based on their personal vector database.

#### 2. Position Recommendation API Endpoint (`backend/main.py`)

- **Changes**:
  - Added `POST /api/recommend-positions` with `RecommendPositionsRequest` schema.
  - Reads aggregated documents across all ChromaDB collections (`experiences`, `projects`, `skills`, `education`, `raw_documents`) and passes the verified context to the LLM.
- **Reason**:
  - Provides a dedicated REST endpoint for the frontend to trigger vector database analysis and receive structured role recommendations.

#### 3. Frontend Role Matches Tab (`frontend/src/components/RoleRecommender.tsx`, `Navbar.tsx`, `page.tsx`)

- **Changes**:
  - Created [`RoleRecommender.tsx`](file:///c:/Users/Joji/2026%20Exp/Resume_builder/frontend/src/components/RoleRecommender.tsx) displaying Fit Scores (%), Seniority Badges, "Why You're Qualified" proof points citing real database records, and recommended application focus areas.
  - Added "Role Matches" tab to [`Navbar.tsx`](file:///c:/Users/Joji/2026%20Exp/Resume_builder/frontend/src/components/Navbar.tsx).
  - Implemented one-click tailoring: clicking "Tailor Resume for this Role" pre-fills the target role title and sample JD into [`JobTailor.tsx`](file:///c:/Users/Joji/2026%20Exp/Resume_builder/frontend/src/components/JobTailor.tsx) and transitions to the tailoring view.
- **Reason**:
  - Delivers a streamlined workflow where candidates discover matching roles and immediately tailor a resume for them without manual copy-pasting.

#### 4. Clarification on Mock vs. Live Data

- **Changes**:
  - Verified live Ollama connectivity on `http://localhost:11434` (`200 OK` response using `gemma4:31b-cloud`).
  - Documented in the UI and walkthrough that ChromaDB runs 100% on local ONNX embeddings (`all-MiniLM-L6-v2`) and the sample data is merely an optional seed profile that can be reset at any time.
- **Reason**:
  - Directly resolved the user's doubt regarding whether mock data was being used.

---

## [v1.0.0] - 2026-09-04

### Summary

Initial release of the privacy-first, retrieval-augmented generation (RAG) Local AI Resume Builder.

### Changes Made & Rationale

#### 1. Root Workspace & Concurrent Runner (`package.json`)

- **Changes**:
  - Configured `concurrently` in the root [`package.json`](file:///c:/Users/Joji/2026%20Exp/Resume_builder/package.json) with `npm run dev` script spawning both the FastAPI backend and Next.js frontend with colored prefixed logs.
- **Reason**:
  - Requested by the user so that the entire full-stack application can be started with a single terminal command.

#### 2. FastAPI Backend & Vector Database (`backend/`)

- **Changes**:
  - Set up Python 3.11 virtual environment via `uv` for binary wheel compatibility.
  - Implemented persistent ChromaDB manager ([`backend/rag/vectorstore.py`](file:///c:/Users/Joji/2026%20Exp/Resume_builder/backend/rag/vectorstore.py)) with separated collections: `experiences`, `projects`, `skills`, `education`, and `raw_documents`.
  - Built ingestion pipeline ([`backend/rag/ingestion.py`](file:///c:/Users/Joji/2026%20Exp/Resume_builder/backend/rag/ingestion.py)) for text/markdown chunking and structured JSON profile ingestion.
  - Implemented RAG retriever ([`backend/rag/retriever.py`](file:///c:/Users/Joji/2026%20Exp/Resume_builder/backend/rag/retriever.py)) with cosine similarity search and JD keyword extraction.
  - Added anti-hallucination system prompts ([`backend/ai/prompts.py`](file:///c:/Users/Joji/2026%20Exp/Resume_builder/backend/ai/prompts.py)) enforcing 100% factual grounding against the candidate's database.
  - Added seed profile ([`backend/sample_data/sample_profile.json`](file:///c:/Users/Joji/2026%20Exp/Resume_builder/backend/sample_data/sample_profile.json)) and CLI ingestion script ([`backend/scripts/ingest_sample.py`](file:///c:/Users/Joji/2026%20Exp/Resume_builder/backend/scripts/ingest_sample.py)).
  - Added GitHub repository ingestion script ([`backend/scripts/ingest_github.py`](file:///c:/Users/Joji/2026%20Exp/Resume_builder/backend/scripts/ingest_github.py)).
- **Reason**:
  - Core privacy-first backend architecture ensuring personal data never leaves the user's computer.

#### 3. Headless PDF Generation (`backend/pdf/`)

- **Changes**:
  - Integrated Playwright Chromium ([`backend/pdf/generator.py`](file:///c:/Users/Joji/2026%20Exp/Resume_builder/backend/pdf/generator.py)) with Jinja2 resume templates ([`backend/pdf/templates.py`](file:///c:/Users/Joji/2026%20Exp/Resume_builder/backend/pdf/templates.py)) supporting "Modern Tech" and "Minimalist Executive" formats.
- **Reason**:
  - Generates pixel-perfect, print-ready A4/Letter PDF resumes directly from tailored resume JSON.

#### 4. Next.js Web Frontend (`frontend/`)

- **Changes**:
  - Initialized Next.js 14 app with TypeScript, Tailwind CSS, and Lucide icons.
  - Built navigation header ([`Navbar.tsx`](file:///c:/Users/Joji/2026%20Exp/Resume_builder/frontend/src/components/Navbar.tsx)) with real-time status pills for Ollama, ChromaDB, and backend connectivity.
  - Built Job Tailor workspace ([`JobTailor.tsx`](file:///c:/Users/Joji/2026%20Exp/Resume_builder/frontend/src/components/JobTailor.tsx)) with sample JDs and candidate override fields.
  - Built Resume Preview & Editor ([`ResumePreview.tsx`](file:///c:/Users/Joji/2026%20Exp/Resume_builder/frontend/src/components/ResumePreview.tsx)) with live template switcher and instant PDF download.
  - Built RAG Provenance Inspector ([`RetrievalMatches.tsx`](file:///c:/Users/Joji/2026%20Exp/Resume_builder/frontend/src/components/RetrievalMatches.tsx)) displaying similarity scores and extracted keywords.
  - Built Knowledge Base manager ([`KnowledgeBase.tsx`](file:///c:/Users/Joji/2026%20Exp/Resume_builder/frontend/src/components/KnowledgeBase.tsx)) to view collection statistics, add notes, and seed or reset the database.
- **Reason**:
  - Provides a clean, modern UI for managing the knowledge base, customizing resumes, and previewing exports.
