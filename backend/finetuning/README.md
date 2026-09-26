# 🎯 Fine-Tuning Guide: High-Performance Resume Tailoring for Ollama

This directory provides an end-to-end toolkit to transform standard open-source models (such as Llama 3 or Mistral) into specialized **Resume Tailoring Architects**.

> Start with [`IMPLEMENTATION.md`](IMPLEMENTATION.md) and run the dataset validator before training. The legacy dataset generator can emit synthetic/placeholder candidate data and must not be used unreviewed.

---

## ⚡ Method 1: Instant Zero-Code Model Setup (Takes 30 Seconds)

If you don't want to spend time training neural network weights, Ollama allows you to "bake" system prompts, parameters, and 8K context limits directly into a custom local model.

1. Open your terminal in this repository.
2. Run:
   ```bash
   ollama create resume-architect -f backend/finetuning/Modelfile
   ```
3. Refresh the web app. You will now see **`resume-architect`** in the model dropdown list!

### What this accomplishes:
- Stores a reusable system prompt in an Ollama model definition.
- Pre-sets `temperature 0.15` and `num_ctx 8192`.
- Encourages the resume JSON shape, but still requires application-side schema validation.

The backend currently also sends its strict system prompt, so the Modelfile does not yet reduce prompt tokens until prompt ownership is made model-aware.

---

## 🚀 Method 2: QLoRA Fine-Tuning (Full Neural Network Adaptation)

True fine-tuning teaches the model the style, brevity, and Google XYZ achievement formula (`Accomplished [X] as measured by [Y], by doing [Z]`) across hundreds of diverse job scenarios.

### Step 1: Generate Training Data
Generate high-quality training pairs tailored to your profile:
```bash
# In the backend directory
python backend/finetuning/dataset_generator.py --count 150 --workers 4 --output backend/data/finetuning/generated_dataset.jsonl
python backend/finetuning/split_dataset.py --source backend/data/finetuning/generated_dataset.jsonl
```
*(Or click **"Export Training Dataset"** in the Connectors Hub within the web application).*

### Step 2: Validate the reviewed dataset

```bash
python backend/finetuning/finetune_llama3.py \
  --dataset backend/data/finetuning/training_data.jsonl \
  --validate-only
```

### Step 3: Run Training

#### Option A: Google Colab T4 (required for the current 6 GB workstation)
1. Open [Google Colab](https://colab.research.google.com/).
2. Click **Upload** and select `backend/finetuning/fine_tune_colab.ipynb`.
3. Set Runtime to **T4 GPU** (`Runtime -> Change runtime type -> T4 GPU`).
4. Run the notebook cells in order:
   - authorize Drive for resumable checkpoints;
   - authenticate to Hugging Face with a read-only token;
   - upload only the approved `training_data.jsonl` when prompted;
   - download the resulting `resume-llama3-lora-adapter.zip`.

The notebook verifies the exact approved dataset SHA-256, refuses the holdout file, records package/model metadata, and exports only the adapter. It intentionally does not merge or create GGUF before holdout evaluation.

If a previous notebook copy fails with `_amp_foreach_non_finite_check_and_unscale_cuda` for `BFloat16`, upload the current notebook again and restart the Colab runtime. The current workflow detects GPU precision support and promotes all trainable LoRA parameters to FP32 before AMP training.

#### Option B: Local Training (Requires an NVIDIA GPU with at least 8 GB VRAM)
```bash
pip install -r backend/finetuning/requirements.txt
python backend/finetuning/finetune_llama3.py \
  --dataset backend/data/finetuning/training_data.jsonl \
  --output backend/finetuning/artifacts/resume-llama3-lora \
  --epochs 3
```

### Step 4: Evaluate the adapter on the untouched holdout

1. Open Colab and upload `backend/finetuning/evaluate_adapter_colab.ipynb`.
2. Select a T4 GPU and run the cells in order.
3. Upload these two files when prompted:
   - `backend/finetuning/artifacts/resume-llama3-lora-adapter.zip`
   - `backend/data/finetuning/holdout_eval.jsonl`
4. Download `adapter_holdout_outputs.json` after all 30 records finish.
5. Copy it to `backend/finetuning/artifacts/adapter_holdout_outputs.json` and run:

```powershell
backend\venv\Scripts\python.exe backend\finetuning\score_adapter_outputs.py
```

The notebook pins the adapter, holdout, training-data, and base-revision hashes; passes only system/user turns into the model; and saves resumable progress to Google Drive after every record. The local scorer validates all record IDs, factual/static rules, exact training-output leakage, and improvement over the recorded baseline. A passing automated report still requires manual review of the generated comparison packet.

### Step 5: Merge, convert, and import into Ollama

The adapter must first pass the holdout gates in `IMPLEMENTATION.md`. Merge it with the exact training base, then import supported merged Safetensors or convert/quantize it to GGUF. The legacy `export_ollama.py` registers an existing GGUF; it does not perform GGUF conversion itself.

Move the generated/downloaded `.gguf` file into `backend/finetuning/`, then run:
```bash
python backend/finetuning/export_ollama.py --model-name resume-tailor
```
Or manually:
```bash
ollama create resume-tailor -f backend/finetuning/Modelfile.exported
```

### Step 6: Use in App
Select **`resume-tailor`** in the model selector on the **Tailor Resume** tab after the exported model passes the same holdout evaluation.
