"""Deterministically split validated JSONL into 80% train / 20% holdout."""

from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path
from typing import Any

CURRENT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = CURRENT_DIR.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from finetuning.finetune_llama3 import DatasetValidationError, load_validated_records  # noqa: E402


def _write_jsonl_atomic(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8", newline="\n") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n")
    temporary.replace(path)


def split_dataset(
    source: Path,
    training_output: Path,
    holdout_output: Path,
    *,
    seed: int = 42,
    train_ratio: float = 0.8,
) -> tuple[int, int]:
    if not 0.5 <= train_ratio <= 0.9:
        raise DatasetValidationError("train_ratio must be between 0.5 and 0.9.")
    if training_output.resolve() == holdout_output.resolve():
        raise DatasetValidationError("Training and holdout outputs must be different files.")
    if source.resolve() in {training_output.resolve(), holdout_output.resolve()}:
        raise DatasetValidationError("Source must differ from both output files.")

    records = load_validated_records(source, min_samples=100)
    random.Random(seed).shuffle(records)
    train_count = round(len(records) * train_ratio)
    training = records[:train_count]
    holdout = records[train_count:]
    if not training or not holdout:
        raise DatasetValidationError("Split produced an empty training or holdout set.")
    _write_jsonl_atomic(training_output, training)
    _write_jsonl_atomic(holdout_output, holdout)
    return len(training), len(holdout)


def main() -> int:
    parser = argparse.ArgumentParser(description="Create deterministic training and holdout JSONL files.")
    parser.add_argument("--source", default="backend/data/finetuning/generated_dataset.jsonl")
    parser.add_argument("--training-output", default="backend/data/finetuning/training_data.jsonl")
    parser.add_argument("--holdout-output", default="backend/data/finetuning/holdout_eval.jsonl")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--train-ratio", type=float, default=0.8)
    args = parser.parse_args()
    try:
        train_count, holdout_count = split_dataset(
            Path(args.source), Path(args.training_output), Path(args.holdout_output),
            seed=args.seed, train_ratio=args.train_ratio,
        )
    except DatasetValidationError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(f"Wrote {train_count} training and {holdout_count} holdout examples.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
