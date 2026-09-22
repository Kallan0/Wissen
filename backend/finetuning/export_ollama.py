"""
Exports Fine-Tuned Model to GGUF and registers it directly with Ollama.

Usage:
    python backend/finetuning/export_ollama.py --adapter backend/finetuning/resume_lora_adapter --model-name resume-tailor
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent

def export_and_register(
    adapter_path: str,
    base_model_name: str = "meta-llama/Meta-Llama-3-8B-Instruct",
    merged_output_dir: str = "backend/finetuning/merged_model",
    gguf_path: str = "backend/finetuning/resume_tailor_q4.gguf",
    ollama_model_name: str = "resume-tailor"
):
    print("=" * 70)
    print("OLLAMA EXPORT & MODEL REGISTRATION")
    print("=" * 70)
    print(f"Adapter:           {adapter_path}")
    print(f"Ollama Model Name: {ollama_model_name}")
    print("=" * 70)

    # 1. Merge LoRA weights if adapter exists
    if Path(adapter_path).exists():
        print("\n[1/3] Merging LoRA adapter with base model...")
        try:
            import importlib
            torch = importlib.import_module("torch")
            transformers = importlib.import_module("transformers")
            AutoModelForCausalLM = getattr(transformers, "AutoModelForCausalLM")
            AutoTokenizer = getattr(transformers, "AutoTokenizer")
            peft = importlib.import_module("peft")
            PeftModel = getattr(peft, "PeftModel")

            print(f"Loading base model: {base_model_name}")
            base_model = AutoModelForCausalLM.from_pretrained(
                base_model_name,
                torch_dtype=torch.float16,
                device_map="auto"
            )
            tokenizer = AutoTokenizer.from_pretrained(base_model_name)

            print(f"Loading adapter: {adapter_path}")
            model = PeftModel.from_pretrained(base_model, adapter_path)
            merged_model = model.merge_and_unload()

            os.makedirs(merged_output_dir, exist_ok=True)
            print(f"Saving merged weights to: {merged_output_dir}")
            merged_model.save_pretrained(merged_output_dir)
            tokenizer.save_pretrained(merged_output_dir)
            print("Merge successful!")
        except Exception as e:
            print(f"Merge step skipped or encountered note: {e}")
            print("If you trained via Unsloth/Colab, the .gguf file is already directly exported.")
    else:
        print(f"Notice: Adapter directory '{adapter_path}' not found locally.")

    # 2. Check for GGUF file
    gguf_file = Path(gguf_path)
    if not gguf_file.exists():
        # Check if user put any .gguf file in backend/finetuning/
        found_ggufs = list(CURRENT_DIR.glob("*.gguf"))
        if found_ggufs:
            gguf_file = found_ggufs[0]
            print(f"Discovered GGUF file: {gguf_file}")
        else:
            print(f"\nNo GGUF file found at '{gguf_path}'.")
            print("If you used the Google Colab notebook, place the downloaded .gguf file in:")
            print(f"  {CURRENT_DIR}/resume_tailor_q4.gguf")
            print("Then re-run this script.")
            return

    # 3. Create Ollama Modelfile for the GGUF model
    modelfile_path = CURRENT_DIR / "Modelfile.exported"
    modelfile_content = f"""# Custom Fine-Tuned Resume Tailor Model
FROM ./{gguf_file.name}

PARAMETER temperature 0.15
PARAMETER top_p 0.90
PARAMETER top_k 40
PARAMETER num_ctx 8192
PARAMETER stop "<|start_header_id|>"
PARAMETER stop "<|end_header_id|>"
PARAMETER stop "<|eot_id|>"

SYSTEM \"\"\"You are an expert AI Resume Architect and Privacy-Preserving Career Strategist.
Your task is to craft a tailored, high-impact resume strictly aligned to a target Job Description (JD) using ONLY the provided verified candidate context.
Output MUST be valid JSON conforming to the resume schema with Google XYZ bullet points.
\"\"\"
"""
    with open(modelfile_path, "w", encoding="utf-8") as f:
        f.write(modelfile_content)

    print(f"\n[2/3] Generated Ollama Modelfile: {modelfile_path}")

    # 4. Register with Ollama
    print(f"\n[3/3] Registering model '{ollama_model_name}' with Ollama...")
    try:
        cmd = ["ollama", "create", ollama_model_name, "-f", str(modelfile_path)]
        result = subprocess.run(cmd, cwd=str(CURRENT_DIR), capture_output=True, text=True)
        if result.returncode == 0:
            print("\n" + "=" * 70)
            print(f"SUCCESS! '{ollama_model_name}' is now registered in Ollama!")
            print(f"You can now select '{ollama_model_name}' in the web app's Model Selector.")
            print("=" * 70)
        else:
            print(f"Ollama command returned code {result.returncode}:")
            print(result.stderr or result.stdout)
            print(f"\nYou can also run it manually from the terminal:")
            print(f"  cd \"{CURRENT_DIR}\"")
            print(f"  ollama create {ollama_model_name} -f Modelfile.exported")
    except FileNotFoundError:
        print("Notice: 'ollama' command line tool not detected in current PATH.")
        print(f"Run manually in your command prompt:\n  cd \"{CURRENT_DIR}\"\n  ollama create {ollama_model_name} -f Modelfile.exported")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Export and register fine-tuned model in Ollama.")
    parser.add_argument("--adapter", type=str, default="backend/finetuning/resume_lora_adapter")
    parser.add_argument("--gguf", type=str, default="backend/finetuning/resume_tailor_q4.gguf")
    parser.add_argument("--model-name", type=str, default="resume-tailor")
    args = parser.parse_args()

    export_and_register(
        adapter_path=args.adapter,
        gguf_path=args.gguf,
        ollama_model_name=args.model_name
    )
