"""Fail-closed preflight checks for the QLoRA training environment."""

from __future__ import annotations

import argparse
import hashlib
import importlib
import importlib.metadata
import json
import shutil
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

CURRENT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = CURRENT_DIR.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from finetuning.finetune_llama3 import (  # noqa: E402
    check_huggingface_model_access,
    load_validated_records,
)


PACKAGES = ("torch", "transformers", "datasets", "accelerate", "peft", "trl", "bitsandbytes")


@dataclass
class Check:
    name: str
    status: str
    detail: str


def _hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_preflight(
    training: Path,
    holdout: Path,
    output: Path,
    min_free_gb: float = 30.0,
    base_model: str | None = None,
) -> dict[str, Any]:
    checks: list[Check] = []
    try:
        train_records = load_validated_records(training, min_samples=100)
        holdout_records = load_validated_records(holdout, min_samples=20)
        checks.append(Check("datasets.valid", "pass", f"{len(train_records)} training / {len(holdout_records)} holdout"))
    except Exception as exc:
        train_records, holdout_records = [], []
        checks.append(Check("datasets.valid", "fail", str(exc)))

    if train_records and holdout_records:
        canonical = lambda record: hashlib.sha256(json.dumps(record, sort_keys=True).encode()).hexdigest()
        overlap = {canonical(item) for item in train_records} & {canonical(item) for item in holdout_records}
        checks.append(Check("datasets.no_overlap", "pass" if not overlap else "fail", f"{len(overlap)} overlapping records"))

    versions: dict[str, str] = {}
    for package in PACKAGES:
        try:
            versions[package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            versions[package] = "missing"
    missing = [name for name, version in versions.items() if version == "missing"]
    checks.append(Check("dependencies", "pass" if not missing else "fail", "missing: " + ", ".join(missing) if missing else "all training packages installed"))

    cuda_detail = "torch unavailable"
    cuda_ok = False
    try:
        torch = importlib.import_module("torch")
        cuda_ok = bool(torch.cuda.is_available())
        if cuda_ok:
            properties = torch.cuda.get_device_properties(0)
            cuda_detail = f"{properties.name}; {properties.total_memory / (1024 ** 3):.1f} GiB VRAM"
        else:
            cuda_detail = "CUDA is not available"
    except Exception as exc:
        cuda_detail = str(exc)
    checks.append(Check("cuda", "pass" if cuda_ok else "fail", cuda_detail))

    if base_model:
        model_ok, model_detail = check_huggingface_model_access(base_model)
        checks.append(Check("model.access", "pass" if model_ok else "fail", model_detail))

    output.parent.mkdir(parents=True, exist_ok=True)
    free_gb = shutil.disk_usage(output.parent).free / (1024 ** 3)
    checks.append(Check("disk_space", "pass" if free_gb >= min_free_gb else "fail", f"{free_gb:.1f} GiB free; {min_free_gb:.1f} GiB required"))
    checks.append(Check("output.not_in_git", "pass" if "artifacts" in output.parts else "warning", str(output)))

    report = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "training_path": str(training),
        "training_sha256": _hash(training) if training.exists() else None,
        "holdout_path": str(holdout),
        "holdout_sha256": _hash(holdout) if holdout.exists() else None,
        "output_path": str(output),
        "base_model": base_model,
        "package_versions": versions,
        "checks": [asdict(check) for check in checks],
        "passed": all(check.status in {"pass", "warning"} for check in checks),
    }
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Check the local environment before QLoRA training.")
    parser.add_argument("--training", default="backend/data/finetuning/training_data.jsonl")
    parser.add_argument("--holdout", default="backend/data/finetuning/holdout_eval.jsonl")
    parser.add_argument("--output", default="backend/finetuning/artifacts/resume-llama3-lora")
    parser.add_argument("--report", default="backend/data/finetuning/reports/training_preflight.json")
    parser.add_argument("--min-free-gb", type=float, default=30.0)
    parser.add_argument("--base-model", default="meta-llama/Meta-Llama-3-8B-Instruct")
    parser.add_argument(
        "--skip-model-access-check",
        action="store_true",
        help="Skip the online Hugging Face authorization check (not recommended before training).",
    )
    args = parser.parse_args()
    report = run_preflight(
        Path(args.training),
        Path(args.holdout),
        Path(args.output),
        args.min_free_gb,
        None if args.skip_model_access_check else args.base_model,
    )
    report_path = Path(args.report)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    for check in report["checks"]:
        print(f"[{check['status'].upper()}] {check['name']}: {check['detail']}")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
