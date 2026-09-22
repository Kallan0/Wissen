# Llama 3 Fine-Tuning Implementation

## Goal

Produce a small, reproducible LoRA adapter that improves valid resume-JSON generation and factual grounding without memorizing placeholder identities or unsupported achievements.

## Implemented entry point

Use `finetune_llama3.py`. It provides:

- strict messages-format JSONL validation;
- required resume-schema checks for assistant responses;
- rejection of known placeholder identities by default;
- exact-example deduplication;
- deterministic train/evaluation splitting;
- QLoRA with NF4 and PEFT `all-linear` targeting;
- fail-fast CUDA detection; and
- a `training_manifest.json` containing configuration, sample counts, and dataset SHA-256.

Ollama hosts quantized inference artifacts. This script therefore trains the compatible Hugging Face base checkpoint and saves an adapter; it does not modify the installed Ollama model directly.

## Data gate

Do not train on the current generator output without review. Build at least 100–200 genuinely distinct examples covering:

1. Different role families and seniority levels.
2. Sparse profiles where sections must stay empty.
3. Job requirements absent from the profile, with outputs that explicitly omit them.
4. Profiles with and without metrics.
5. Long context, unusual dates, links, and optional contact fields.
6. Adversarial JDs that ask the model to invent credentials.

Every output must be valid JSON and every factual phrase must be supported by its input context. Keep a separately authored holdout set that never enters training.

The current 50-record generated dataset passes structural validation, but it is not suitable for training: it contains no experience bodies and repeats one project body across all samples. Structural validation is a floor, not a substitute for semantic review and diversity.

The generator now refuses to replace this file until ChromaDB contains a verified candidate name, at least one experience record, and verified skills. After those fields are populated, generate and split 150 examples with:

```powershell
backend\venv\Scripts\python.exe backend\finetuning\dataset_generator.py `
  --count 150 `
  --workers 4 `
  --output backend\data\finetuning\generated_dataset.jsonl

backend\venv\Scripts\python.exe backend\finetuning\split_dataset.py `
  --source backend\data\finetuning\generated_dataset.jsonl
```

### Completed dataset run

The 150-example run completed successfully on 2026-09-21 using local `llama3:latest`. Python injected deterministic identity and profile metadata after Ollama generated only the prose fields. The resulting files contain 120 training examples and 30 holdout examples with zero exact overlap and a balanced 50/50/50 role distribution.

## Commands

Create a dedicated GPU environment and install the training dependencies:

```powershell
python -m venv .venv-train
.\.venv-train\Scripts\python.exe -m pip install -r backend\finetuning\requirements.txt
```

Validate data on any machine before allocating GPU time:

```powershell
backend\venv\Scripts\python.exe backend\finetuning\finetune_llama3.py `
  --dataset backend\data\finetuning\training_data.jsonl `
  --validate-only
```

Train on Linux/WSL or a CUDA-enabled environment:

```bash
python backend/finetuning/finetune_llama3.py \
  --dataset backend/data/finetuning/training_data.jsonl \
  --base-model meta-llama/Meta-Llama-3-8B-Instruct \
  --output backend/finetuning/artifacts/resume-llama3-lora \
  --epochs 3
```

The exact base checkpoint must match the weights used for merge/export. Access to Meta’s gated Hugging Face checkpoint may require accepting its license and authenticating with Hugging Face.

## Evaluation gates

Compare the untouched base model and the adapter on the same holdout prompts. Do not import the adapter into Ollama unless all gates pass:

| Metric | Minimum gate |
|---|---:|
| Parseable JSON | 100% |
| Required schema fields present | 100% |
| Unsupported factual claims | 0 |
| Contact/identity corruption | 0 |
| Exact training-output leakage | 0 |
| Holdout loss | Better than base/baseline run |

Also review bullet usefulness and keyword relevance manually. ATS keyword gain is not a success if the added keyword is unsupported.

## Ollama deployment

1. Merge the saved adapter into the **same** base checkpoint used for training.
2. Either import a supported merged Safetensors directory or convert with llama.cpp and quantize to a GGUF such as Q4_K_M.
3. Point a Modelfile `FROM` instruction at that artifact.
4. Run `ollama create resume-tailor -f <Modelfile>`.
5. Run the full holdout suite through Ollama and compare with the pre-export adapter.
6. Set `OLLAMA_DEFAULT_MODEL=resume-tailor` only after parity passes.

The legacy `export_ollama.py` currently registers an existing GGUF but does not itself perform GGUF conversion or quantization; treat it as a registration helper until that gap is fixed.
