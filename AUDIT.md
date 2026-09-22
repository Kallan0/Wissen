# Repository Audit — 2026-09-21

## Executive summary

The application has a coherent local-first architecture and the frontend builds successfully, but the current fine-tuning path should **not** be run on personal data yet. The largest risks are destructive tests pointed at the persistent ChromaDB, synthetic/placeholder data entering training, a version-incompatible QLoRA script, and an export script that claims to convert to GGUF without performing that conversion.

This audit covered all readable source/configuration files under `backend/`, `frontend/`, the root workspace, and `versions/`. Generated dependencies (`node_modules`), binary assets, ChromaDB data, build outputs, and OS-locked pytest temporary folders were inventoried but not treated as reviewable source.

## Findings

| Severity | Area | Finding | Evidence / impact | Recommended action |
|---|---|---|---|---|
| Critical | Tests / data safety | The E2E suite clears the configured persistent knowledge base before and after every test. | `backend/tests/test_e2e.py` uses the real app/settings and an autouse fixture calls `/api/knowledge-base/clear`. Running the suite can erase the candidate profile. | Inject a temporary `CHROMA_DIR` before app import and assert it is under a test-only directory. Do not run the current full suite against real data. |
| High | Fine-tuning data | Dataset generation silently falls back to a fabricated “Alex Chen” profile and also inserts placeholder contact data into otherwise real records. | `backend/finetuning/dataset_generator.py`; these outputs can teach the model false identity and achievements. | Require an explicit reviewed profile. Keep synthetic data in a separately labelled fixture that cannot be exported through the production API. |
| High | Fine-tuning quality | Generated samples are templated near-duplicates, use only six base job descriptions, and create summaries that may claim distributed systems, latency, and CI/CD regardless of source evidence. | `synthesize_tailored_resume()` and `build_dataset()` in `dataset_generator.py`. The existing 50-sample dataset has 29 titles but no experience bodies and only one unique project body. Fine-tuning would reinforce repetition and may reinforce hallucinations. | Curate diverse, human-reviewed examples; add unsupported-claim negatives; deduplicate semantically; reserve an independently authored evaluation set. |
| High | Training implementation | The existing trainer wraps the model with PEFT and also passes `peft_config` to `SFTTrainer`; it also uses older TRL constructor arguments. | `backend/finetuning/train_lora.py`. Depending on installed TRL/PEFT versions, training will fail or double-apply adapters. | Use `finetune_llama3.py`, which follows the current `SFTConfig`/`SFTTrainer` path and applies PEFT once. |
| High | Model export | `export_ollama.py` merges an adapter but never converts or quantizes the merged model to GGUF. It only succeeds if a GGUF already exists. | The script’s name/output text promises conversion that its code does not perform. | Add a real llama.cpp conversion/quantization step or import supported merged Safetensors directly. Verify base-model compatibility before merge. |
| High | Network security | The API binds to `0.0.0.0`, permits wildcard CORS, exposes destructive KB operations, and can scan caller-supplied local filesystem paths without authentication. | `backend/main.py`. On an untrusted LAN, another origin may invoke local endpoints. | Default to loopback, restrict CORS to the frontend origin, add authentication/CSRF protection before LAN exposure, and allow-list scan roots. |
| High | Grounding | The offline fallback inserts default skills and generic achievements not present in the candidate record. | `_build_fallback_resume()` in `backend/ai/generator.py` adds Python/TypeScript/FastAPI/React/SQL and generated deliverables. | Return empty sections or explicit “insufficient evidence” errors; never manufacture resume facts. |
| Medium | Prompt/model consistency | The custom Modelfile embeds the full system prompt, while the backend still prepends `STRICT_SYSTEM_PROMPT`. | `backend/finetuning/Modelfile` plus `backend/ai/generator.py`. This wastes context and can bias/repeat output. | Choose one system-prompt owner and add model-specific prompt configuration. |
| Medium | Model selection | Defaults and UI special-case the literal `llama3`; installed tags commonly include a tag suffix, and the selected training base may not match the Ollama artifact. | `backend/config.py`, `backend/ai/generator.py`, and frontend selectors. | Store an exact model ID/tag in configuration and record it in the training/export manifest. |
| Medium | Output validation | LLM JSON is parsed but not validated against a Pydantic resume schema before reaching the UI/PDF layer. | `extract_json()` accepts any object. | Define one shared response schema and reject/repair invalid shapes before rendering. |
| Medium | Dependency reproducibility | Runtime dependencies use broad lower bounds; test dependencies are undocumented in the actual requirements file; ML dependencies were previously only shown as an unpinned command. | `backend/requirements.txt` and the prior fine-tuning README. | Use lock files or tested upper/lower ranges and separate runtime, test, and training environments. |
| Medium | Text integrity | Multiple tracked files contain mojibake such as `â€”`, `â€¢`, and broken emoji bytes. | Backend comments/strings, test docs, templates, changelog, and fine-tuning docs. | Normalize files to UTF-8 and add an encoding scan to CI. |
| Medium | Error handling | Many broad `except Exception` blocks convert programming/data errors into fallbacks. | Generator, vector store, connectors, and API endpoints. | Catch expected exceptions, preserve cause/status, and surface actionable errors. |
| Low | Documentation drift | Root README describes roadmap items already implemented and names architecture pieces no longer used in the generation path. | `README.md`. | Update architecture/setup after stabilizing the current feature branch. |
| Low | Repository hygiene | Build artifacts, pytest temp directories, `tsconfig.tsbuildinfo`, and generated model/data paths are present or untracked. | Working tree inventory. | Expand `.gitignore`; keep model weights, adapters, GGUF, datasets, and personal ChromaDB out of Git. |

## Verification performed

- `npm.cmd run build` in `frontend/`: **passed**, including TypeScript and Next.js production compilation. Google Fonts optimization was skipped because the stylesheet could not be downloaded in the restricted environment.
- Python compilation for readable backend source: **passed**. Locked pytest/cache folders produced directory-access warnings only.
- Pytest collection: **50 existing tests collected** without running destructive fixtures.
- New fine-tuning validation tests: **3 passed**.
- Existing `training_data.jsonl`: **50 structurally valid unique records**, split reproducibly into 45 train / 5 evaluation by the new validator. It is **not training-ready** because content diversity is inadequate (zero experience bodies and one unique project body across all samples).
- Full E2E execution: **intentionally not run** because its fixture targets and clears the persistent knowledge base.

## Fine-tuning decision

Fine-tuning is reasonable only after the data path is corrected. The model running in Ollama cannot be trained “in place”; train the exact compatible Hugging Face base checkpoint with QLoRA, evaluate the adapter, merge/export it, quantize to GGUF (or import a supported merged Safetensors directory), then create a new Ollama model. The implementation and acceptance gates are in `backend/finetuning/IMPLEMENTATION.md`.
