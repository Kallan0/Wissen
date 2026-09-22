# Fine-Tuning: Next Implementation Plan

## Objective

Train, evaluate, export, and safely integrate a resume-specialized Llama 3 model using the completed dataset:

- 120 training examples: `backend/data/finetuning/training_data.jsonl`
- 30 untouched evaluation examples: `backend/data/finetuning/holdout_eval.jsonl`
- Zero exact overlap between the two files
- 50 combined examples for each target role family

The holdout file must never be used for training, prompt demonstrations, checkpoint selection by hand, or dataset regeneration.

## Current progress

- Phase 1 automated auditor: **complete**.
- Current audit: **0 hard errors, 2 warning categories**.
- Static identity/profile validation: **passed**.
- Training/holdout overlap: **0**.
- Manual review packet: **generated with 30 records**.
- Manual approval: **complete — 30/30 accepted**.
- Phase 1 gate: **complete**.
- Phase 2 evaluation harness: **implemented**.
- Baseline inference run: **invalid — Ollama connection refused for 30/30 records; rerun required**.
- Phase 3 training preflight: **implemented and executed**.
- Dataset separation and disk space: **passed**.
- Local ML dependencies and CUDA: **failed/not installed**.

## Ownership rule

Tasks requiring significant elapsed time, private-data judgment, external authentication, GPU access, large downloads, or subjective approval are marked **MANUAL**. All implementation, automation, validation, integration, and defect remediation tasks are marked **CODEX**.

## Phase 1 — Dataset quality gate

### CODEX

1. Create `audit_dataset.py` to inspect both JSONL files without modifying them.
2. Verify:
   - valid JSON and required schema fields;
   - exact candidate-name consistency;
   - contact, employer, role, dates, education, project names, links, and technology lists match verified profile records;
   - training/holdout hashes do not overlap;
   - role counts remain balanced;
   - duplicated summaries and bullets are reported;
   - suspicious new metrics, employers, qualifications, and technologies are flagged;
   - empty or unusually long fields are reported.
3. Produce a machine-readable audit report under `backend/data/finetuning/reports/`.
4. Add unit tests for every audit rule.

### MANUAL — approximately 45–90 minutes

1. Review at least 30 records: 10 randomly selected examples from each role family.
2. Compare every summary and bullet with the real resume/profile evidence.
3. Mark each reviewed example as `accept`, `edit`, or `reject`.
4. Confirm whether quantified statements and design claims are genuinely supportable.

### Exit gate

- Zero static-profile mismatches.
- Zero train/holdout overlap.
- No known unsupported claims.
- At least 30 examples manually reviewed.
- Rejected examples removed and the split regenerated if necessary.

## Phase 2 — Baseline evaluation

### CODEX

1. Create `evaluate_model.py` that runs an Ollama model against the 30 holdout prompts.
2. Capture raw responses, parsed outputs, latency, model tag, generation settings, and dataset SHA-256.
3. Score:
   - JSON parse rate;
   - schema-valid rate;
   - exact-name preservation;
   - static-field preservation;
   - unsupported-skill and unsupported-metric counts;
   - empty-section handling;
   - role-keyword relevance;
   - duplicate/repetitive bullet rate.
4. Save results as versioned JSON and Markdown reports.
5. Add a comparison command for baseline versus fine-tuned results.

### MANUAL — approximately 20–60 minutes of local inference

Run the baseline against the untouched holdout set using the exact Ollama base model intended for comparison. Do not edit the holdout responses.

```powershell
backend\venv\Scripts\python.exe backend\finetuning\evaluate_model.py `
  --model llama3:latest `
  --holdout backend\data\finetuning\holdout_eval.jsonl `
  --output-dir backend\data\finetuning\reports\evaluations `
  --workers 2
```

### Exit gate

- Baseline report exists with exact model tag and dataset hash.
- All 30 holdout prompts completed.
- Raw outputs are retained locally for later comparison.

## Phase 3 — Training preparation

### CODEX

1. Pin a tested training environment and record package versions.
2. Add a preflight command that checks:
   - CUDA availability and VRAM;
   - Hugging Face model access;
   - dataset and output paths;
   - available disk space;
   - training/holdout separation;
   - resumable checkpoint configuration.
3. Add resume-from-checkpoint support.
4. Record training configuration and dataset hash before the first optimizer step.
5. Ensure the holdout file is never passed to `SFTTrainer`; use a training-only validation subset if loss monitoring is needed.

### MANUAL — potentially 30 minutes to several hours

1. Choose the training machine: NVIDIA GPU on Linux/WSL or a private Colab/runtime.
2. Accept the Meta Llama license in the browser, then authenticate the exact training environment:

   ```powershell
   .\.venv-train\Scripts\hf.exe auth login
   .\.venv-train\Scripts\hf.exe auth whoami
   ```

   Never paste or commit a Hugging Face token into this repository.
3. Install/download CUDA, PyTorch, the base model, and training dependencies.
4. Confirm there is enough disk space for base weights, checkpoints, merged weights, and GGUF output.
5. Decide whether uploading this private dataset to a hosted notebook is acceptable. Prefer a local GPU when privacy is required.

### Exit gate

- Preflight passes.
- `model.access` reports `PASS` for the selected base model.
- Exact base checkpoint is recorded.
- Training configuration is frozen.
- Sufficient storage and GPU memory are available.

## Phase 4 — QLoRA training

### CODEX

1. Provide the final training command and configuration.
2. Ensure checkpoints and logs are written outside Git.
3. Add automatic failure diagnostics and checkpoint-resume instructions.
4. After training, validate that the PEFT adapter and tokenizer files are complete.
5. Produce a training summary containing duration, loss history, dataset hash, package versions, and artifact hashes.

### MANUAL — potentially 30 minutes to several hours

1. Start and monitor the GPU training job.
2. Keep the machine awake and ensure adequate cooling/power.
3. Resume from the latest checkpoint if the runtime disconnects.
4. Retain the full terminal/trainer log.

### Initial training configuration

```bash
python backend/finetuning/finetune_llama3.py \
  --dataset backend/data/finetuning/training_data.jsonl \
  --base-model meta-llama/Meta-Llama-3-8B-Instruct \
  --output backend/finetuning/artifacts/resume-llama3-lora \
  --epochs 3 \
  --batch-size 1 \
  --gradient-accumulation-steps 8 \
  --learning-rate 1e-4 \
  --max-length 4096
```

### Exit gate

- Training completes without NaN/inf loss.
- Adapter, tokenizer, and manifest exist.
- Dataset hash matches the approved 120-record training file.
- No holdout record entered training.

## Phase 5 — Fine-tuned evaluation

### CODEX

1. Run the same automated evaluation contract used for the baseline.
2. Generate a side-by-side report with per-example regressions and improvements.
3. Fail the release automatically if identity/static fields drift or unsupported claims increase.
4. Recommend retraining parameters only from measured results, not subjective guesswork.

### MANUAL — approximately 45–90 minutes

1. Blind-review baseline and fine-tuned outputs for all 30 holdout prompts.
2. Judge clarity, truthfulness, role relevance, natural wording, and repetition.
3. Approve or reject the adapter for export.

### Acceptance gates

| Metric | Required result |
|---|---:|
| JSON parse rate | 100% |
| Resume schema validity | 100% |
| Candidate-name accuracy | 100% |
| Static-profile accuracy | 100% |
| Unsupported employers/education/skills/metrics | 0 |
| Training/holdout leakage | 0 |
| Role relevance | Better than or equal to baseline |
| Repetition rate | Better than or equal to baseline |

If any factual-safety gate fails, do not export the model.

## Phase 6 — Merge and Ollama export

### CODEX

1. Replace the misleading legacy export flow with an explicit pipeline:
   - verify adapter/base compatibility;
   - merge adapter into the exact training base;
   - save merged Safetensors;
   - optionally convert with llama.cpp;
   - quantize to a named GGUF level;
   - calculate artifact hashes;
   - generate a correct Ollama Modelfile;
   - register under a versioned model name.
2. Remove duplicated system-prompt ownership between the backend and Modelfile.
3. Add a smoke test that sends structured resume prompts through the exported Ollama model.

### MANUAL — potentially 30 minutes to several hours

1. Run the large merge/conversion/quantization operations.
2. Ensure sufficient disk space; merged and intermediate weights can require tens of gigabytes.
3. Confirm the desired quality/speed tradeoff, initially comparing Q4_K_M and Q5_K_M if resources allow.

### Exit gate

- Exported Ollama output matches the pre-export adapter on the holdout suite.
- Quantization does not break JSON/schema or factual-safety gates.
- Model is registered with a versioned name such as `resume-tailor:v1`.

## Phase 7 — Application integration

### CODEX

1. Add the versioned model to configuration without silently replacing the base model.
2. Add Pydantic validation for every generated resume response.
3. Remove hallucinated skills and achievements from the offline fallback.
4. Make system-prompt ownership model-aware to prevent duplicated prompts.
5. Add inference timeouts, error reporting, and a safe fallback that returns missing evidence instead of invented content.
6. Isolate the E2E ChromaDB fixture so tests cannot clear the real knowledge base.
7. Add integration tests for tailoring, role recommendations, ATS analysis, cover letters, and PDF generation with the new model.

### MANUAL — approximately 20–40 minutes

1. Generate several real resumes through the UI.
2. Inspect layout, content truthfulness, PDF output, and response time.
3. Approve changing `OLLAMA_DEFAULT_MODEL` to the versioned fine-tuned model.

### Exit gate

- Automated backend/frontend tests pass.
- Real knowledge-base data is protected during tests.
- Manual UI/PDF smoke test passes.
- Rollback to `llama3:latest` remains a one-setting change.

## Phase 8 — Release and monitoring

### CODEX

1. Produce final release notes, checksums, model card, known limitations, and rollback instructions.
2. Add a local evaluation command that can be rerun after dataset/model changes.
3. Record the approved dataset hash, adapter hash, GGUF hash, Ollama tag, and evaluation report.

### MANUAL — ongoing

1. Review real outputs periodically and save failures as candidate future evaluation cases.
2. Do not add those failures to training until they are corrected and the holdout strategy is reconsidered.
3. Approve any future dataset expansion or retraining cycle.

## Immediate execution order

1. **CODEX:** implement the dataset audit and factual-consistency report.
2. **MANUAL:** review 30 sampled records and approve or correct them.
3. **CODEX:** implement the baseline/fine-tuned evaluation harness.
4. **MANUAL:** run the baseline evaluation if local inference time is substantial.
5. **CODEX:** finalize training preflight, checkpointing, and reproducibility metadata.
6. **MANUAL:** provision/authenticate the GPU environment and run training.
7. **CODEX:** analyze results, implement safe export, integrate the approved model, and complete automated verification.
8. **MANUAL:** approve the holdout results, exported model, and final UI/PDF behavior.

No training should begin until Phase 1 is approved.
