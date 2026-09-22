"""Validated QLoRA fine-tuning entry point for the resume-tailoring model.

This script trains a Hugging Face Llama 3 Instruct checkpoint and writes a
PEFT adapter. Ollama's quantized ``llama3`` model is an inference artifact and
is not trained in place; the resulting adapter must be merged/exported to GGUF
before it is imported into Ollama.

Validation only (safe on a CPU-only workstation):
    python backend/finetuning/finetune_llama3.py \
        --dataset backend/data/finetuning/training_data.jsonl \
        --validate-only

Training (Linux/WSL with an NVIDIA GPU):
    python backend/finetuning/finetune_llama3.py \
        --dataset backend/data/finetuning/training_data.jsonl \
        --output backend/finetuning/artifacts/resume-llama3-lora
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


REQUIRED_RESUME_KEYS = {
    "name",
    "title",
    "contact",
    "summary",
    "skills",
    "experience",
    "projects",
    "education",
}
EXPECTED_ROLES = ("system", "user", "assistant")
PLACEHOLDER_MARKERS = (
    "alex chen",
    "candidate name",
    "candidate@example.com",
    "your name",
    "your.email@example.com",
    "555) 000-0000",
)

HF_LOGIN_COMMAND = r".\.venv-train\Scripts\hf.exe auth login"


class DatasetValidationError(ValueError):
    """Raised when training data would produce an unsafe or invalid adapter."""


def check_huggingface_model_access(repo_id: str) -> tuple[bool, str]:
    """Verify that the active Hugging Face identity can read a model repository."""
    try:
        from huggingface_hub import hf_hub_download
        from huggingface_hub.errors import GatedRepoError, HfHubHTTPError
    except ImportError:
        return False, "huggingface_hub is not installed in the active training environment"

    try:
        hf_hub_download(repo_id=repo_id, filename="config.json")
    except GatedRepoError:
        return False, (
            f"Access to gated model {repo_id!r} was denied. Accept its terms in a browser, "
            f"then authenticate this environment with: {HF_LOGIN_COMMAND}"
        )
    except HfHubHTTPError as exc:
        status_code = getattr(getattr(exc, "response", None), "status_code", None)
        if status_code in {401, 403}:
            return False, (
                f"Hugging Face returned HTTP {status_code} for {repo_id!r}. Confirm that your "
                f"account has model access, then run: {HF_LOGIN_COMMAND}"
            )
        return False, f"Could not verify Hugging Face model {repo_id!r}: {exc}"
    except Exception as exc:
        return False, f"Could not verify Hugging Face model {repo_id!r}: {exc}"

    return True, f"access granted to {repo_id} (config.json readable)"


@dataclass(frozen=True)
class TrainingConfig:
    dataset: str
    output: str
    base_model: str = "meta-llama/Meta-Llama-3-8B-Instruct"
    epochs: float = 3.0
    batch_size: int = 1
    gradient_accumulation_steps: int = 8
    learning_rate: float = 1e-4
    max_length: int = 4096
    eval_ratio: float = 0.1
    seed: int = 42
    min_samples: int = 20
    allow_placeholders: bool = False


def _canonical_digest(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _validate_messages(messages: Any, line_number: int, allow_placeholders: bool) -> None:
    if not isinstance(messages, list) or len(messages) != 3:
        raise DatasetValidationError(
            f"Line {line_number}: 'messages' must contain exactly system, user, and assistant turns."
        )

    roles = tuple(message.get("role") for message in messages if isinstance(message, dict))
    if roles != EXPECTED_ROLES:
        raise DatasetValidationError(
            f"Line {line_number}: roles must be {EXPECTED_ROLES}; received {roles}."
        )

    for message in messages:
        content = message.get("content")
        if not isinstance(content, str) or not content.strip():
            raise DatasetValidationError(
                f"Line {line_number}: every message must have non-empty string content."
            )

    assistant_text = messages[-1]["content"].strip()
    try:
        assistant_payload = json.loads(assistant_text)
    except json.JSONDecodeError as exc:
        raise DatasetValidationError(
            f"Line {line_number}: assistant content is not valid JSON ({exc.msg})."
        ) from exc

    if not isinstance(assistant_payload, dict):
        raise DatasetValidationError(f"Line {line_number}: assistant JSON must be an object.")

    missing = sorted(REQUIRED_RESUME_KEYS - assistant_payload.keys())
    if missing:
        raise DatasetValidationError(
            f"Line {line_number}: assistant JSON is missing required keys: {', '.join(missing)}."
        )

    for key in ("skills", "experience", "projects", "education"):
        if not isinstance(assistant_payload[key], list):
            raise DatasetValidationError(f"Line {line_number}: '{key}' must be a JSON array.")

    if not isinstance(assistant_payload["contact"], dict):
        raise DatasetValidationError(f"Line {line_number}: 'contact' must be a JSON object.")

    if not allow_placeholders:
        normalized = assistant_text.casefold()
        marker = next((item for item in PLACEHOLDER_MARKERS if item in normalized), None)
        if marker:
            raise DatasetValidationError(
                f"Line {line_number}: placeholder/synthetic marker {marker!r} detected. "
                "Replace it with reviewed data or pass --allow-placeholders explicitly."
            )


def load_validated_records(
    dataset_path: Path,
    *,
    min_samples: int = 20,
    allow_placeholders: bool = False,
) -> list[dict[str, Any]]:
    """Load, schema-check, and deduplicate an SFT JSONL dataset."""
    if not dataset_path.is_file():
        raise DatasetValidationError(f"Dataset not found: {dataset_path}")
    if min_samples < 2:
        raise DatasetValidationError("min_samples must be at least 2.")

    records: list[dict[str, Any]] = []
    seen: set[str] = set()
    with dataset_path.open("r", encoding="utf-8-sig") as handle:
        for line_number, raw_line in enumerate(handle, start=1):
            if not raw_line.strip():
                continue
            try:
                record = json.loads(raw_line)
            except json.JSONDecodeError as exc:
                raise DatasetValidationError(
                    f"Line {line_number}: invalid JSONL record ({exc.msg})."
                ) from exc
            if not isinstance(record, dict):
                raise DatasetValidationError(f"Line {line_number}: each JSONL record must be an object.")

            _validate_messages(record.get("messages"), line_number, allow_placeholders)
            digest = _canonical_digest(record["messages"])
            if digest not in seen:
                seen.add(digest)
                records.append({"messages": record["messages"]})

    if len(records) < min_samples:
        raise DatasetValidationError(
            f"Only {len(records)} unique valid samples remain; at least {min_samples} are required. "
            "Do not compensate by duplicating examples."
        )
    return records


def split_records(
    records: Iterable[dict[str, Any]], eval_ratio: float, seed: int
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Create reproducible, non-overlapping train and evaluation splits."""
    if not 0.05 <= eval_ratio <= 0.4:
        raise DatasetValidationError("eval_ratio must be between 0.05 and 0.4.")
    shuffled = list(records)
    random.Random(seed).shuffle(shuffled)
    eval_count = max(1, round(len(shuffled) * eval_ratio))
    if eval_count >= len(shuffled):
        raise DatasetValidationError("Evaluation split leaves no training samples.")
    return shuffled[eval_count:], shuffled[:eval_count]


def _format_records(records: list[dict[str, Any]], tokenizer: Any) -> list[dict[str, str]]:
    formatted: list[dict[str, str]] = []
    for record in records:
        text = tokenizer.apply_chat_template(
            record["messages"], tokenize=False, add_generation_prompt=False
        )
        formatted.append({"text": text})
    return formatted


def train(config: TrainingConfig) -> None:
    records = load_validated_records(
        Path(config.dataset),
        min_samples=config.min_samples,
        allow_placeholders=config.allow_placeholders,
    )
    train_records, eval_records = split_records(records, config.eval_ratio, config.seed)

    try:
        import torch
        from datasets import Dataset
        from peft import LoraConfig, prepare_model_for_kbit_training
        from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
        from trl import SFTConfig, SFTTrainer
    except ImportError as exc:
        raise RuntimeError(
            "Training dependencies are missing. Install the pinned packages listed in "
            "backend/finetuning/requirements.txt."
        ) from exc

    if not torch.cuda.is_available():
        raise RuntimeError(
            "QLoRA training requires a CUDA-capable NVIDIA GPU. Use Linux/WSL or the Colab workflow; "
            "dataset validation can run anywhere with --validate-only."
        )

    model_accessible, access_detail = check_huggingface_model_access(config.base_model)
    if not model_accessible:
        raise RuntimeError(access_detail)
    print(f"Hugging Face model check passed: {access_detail}")

    use_bf16 = bool(torch.cuda.is_bf16_supported())
    quantization = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16 if use_bf16 else torch.float16,
        bnb_4bit_use_double_quant=True,
    )
    tokenizer = AutoTokenizer.from_pretrained(config.base_model, use_fast=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "right"

    model = AutoModelForCausalLM.from_pretrained(
        config.base_model,
        quantization_config=quantization,
        device_map="auto",
        torch_dtype=torch.bfloat16 if use_bf16 else torch.float16,
    )
    model.config.use_cache = False
    model = prepare_model_for_kbit_training(model)

    train_dataset = Dataset.from_list(_format_records(train_records, tokenizer))
    eval_dataset = Dataset.from_list(_format_records(eval_records, tokenizer))
    lora_config = LoraConfig(
        r=16,
        lora_alpha=32,
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM",
        target_modules="all-linear",
    )
    training_args = SFTConfig(
        output_dir=config.output,
        dataset_text_field="text",
        max_length=config.max_length,
        num_train_epochs=config.epochs,
        per_device_train_batch_size=config.batch_size,
        per_device_eval_batch_size=1,
        gradient_accumulation_steps=config.gradient_accumulation_steps,
        learning_rate=config.learning_rate,
        lr_scheduler_type="cosine",
        warmup_ratio=0.03,
        logging_steps=5,
        eval_strategy="epoch",
        save_strategy="epoch",
        save_total_limit=2,
        bf16=use_bf16,
        fp16=not use_bf16,
        optim="paged_adamw_8bit",
        gradient_checkpointing=True,
        report_to="none",
        seed=config.seed,
        data_seed=config.seed,
    )
    trainer = SFTTrainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=eval_dataset,
        peft_config=lora_config,
        processing_class=tokenizer,
    )
    trainer.train()

    output_dir = Path(config.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    trainer.save_model(str(output_dir))
    tokenizer.save_pretrained(str(output_dir))
    manifest = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "training_config": asdict(config),
        "dataset_sha256": hashlib.sha256(Path(config.dataset).read_bytes()).hexdigest(),
        "unique_samples": len(records),
        "train_samples": len(train_records),
        "eval_samples": len(eval_records),
        "artifact_type": "peft_lora_adapter",
    }
    (output_dir / "training_manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate and QLoRA-fine-tune Llama 3 for resume tailoring.")
    parser.add_argument("--dataset", required=True, help="Path to reviewed messages-format JSONL data.")
    parser.add_argument("--output", default="backend/finetuning/artifacts/resume-llama3-lora")
    parser.add_argument("--base-model", default="meta-llama/Meta-Llama-3-8B-Instruct")
    parser.add_argument("--epochs", type=float, default=3.0)
    parser.add_argument("--batch-size", type=int, default=1)
    parser.add_argument("--gradient-accumulation-steps", type=int, default=8)
    parser.add_argument("--learning-rate", type=float, default=1e-4)
    parser.add_argument("--max-length", type=int, default=4096)
    parser.add_argument("--eval-ratio", type=float, default=0.1)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--min-samples", type=int, default=20)
    parser.add_argument("--allow-placeholders", action="store_true")
    parser.add_argument("--validate-only", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    config = TrainingConfig(
        dataset=args.dataset,
        output=args.output,
        base_model=args.base_model,
        epochs=args.epochs,
        batch_size=args.batch_size,
        gradient_accumulation_steps=args.gradient_accumulation_steps,
        learning_rate=args.learning_rate,
        max_length=args.max_length,
        eval_ratio=args.eval_ratio,
        seed=args.seed,
        min_samples=args.min_samples,
        allow_placeholders=args.allow_placeholders,
    )
    try:
        records = load_validated_records(
            Path(config.dataset),
            min_samples=config.min_samples,
            allow_placeholders=config.allow_placeholders,
        )
        train_records, eval_records = split_records(records, config.eval_ratio, config.seed)
        print(
            f"Validated {len(records)} unique samples "
            f"({len(train_records)} train / {len(eval_records)} evaluation)."
        )
        if not args.validate_only:
            train(config)
    except (DatasetValidationError, RuntimeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
