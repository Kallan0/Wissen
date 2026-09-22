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

#### Option A: Free Google Colab (Recommended for everyone)
1. Open [Google Colab](https://colab.research.google.com/).
2. Click **Upload** and select `backend/finetuning/fine_tune_colab.ipynb`.
3. Set Runtime to **T4 GPU** (`Runtime -> Change runtime type -> T4 GPU`).
4. Run the notebook cells:
   - When prompted, upload `training_data.jsonl`.
   - The notebook will train using Unsloth in ~15 minutes.
   - It will automatically convert the weights to GGUF format (`resume_tailor_q4.gguf`) and download it to your computer.

#### Option B: Local Training (Requires NVIDIA GPU with >= 8GB VRAM)
```bash
pip install -r backend/finetuning/requirements.txt
python backend/finetuning/finetune_llama3.py \
  --dataset backend/data/finetuning/training_data.jsonl \
  --output backend/finetuning/artifacts/resume-llama3-lora \
  --epochs 3
```

### Step 4: Evaluate, merge, convert, and import into Ollama

The adapter must first pass the holdout gates in `IMPLEMENTATION.md`. Merge it with the exact training base, then import supported merged Safetensors or convert/quantize it to GGUF. The legacy `export_ollama.py` registers an existing GGUF; it does not perform GGUF conversion itself.

Move the generated/downloaded `.gguf` file into `backend/finetuning/`, then run:
```bash
python backend/finetuning/export_ollama.py --model-name resume-tailor
```
Or manually:
```bash
ollama create resume-tailor -f backend/finetuning/Modelfile.exported
```

### Step 5: Use in App
Select **`resume-tailor`** in the model selector on the **Tailor Resume** tab after the exported model passes the same holdout evaluation.
