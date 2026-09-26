"""Score pre-merge PEFT adapter outputs produced by the Colab evaluation notebook."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

CURRENT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = CURRENT_DIR.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from finetuning.dataset_generator import load_candidate_profile  # noqa: E402
from finetuning.evaluate_model import _record_id, summarize_results  # noqa: E402
from finetuning.finetune_llama3 import load_validated_records  # noqa: E402

EXPECTED_ADAPTER_SHA256 = "eaf9efd5c0f29421d17e9a4a87a546f671f4913b2551addeb1e15c18790982c1"
EXPECTED_HOLDOUT_SHA256 = "8d25b49f6d706254b61f9361e56592185b674a79af504175bcf65888484e1d72"
EXPECTED_BASE_MODEL = "meta-llama/Meta-Llama-3-8B-Instruct"
EXPECTED_BASE_REVISION = "8afb486c1db24fe5011ec46dfbe5b5dccdb575c2"


def _canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected a JSON object in {path}.")
    return value


def score_adapter_outputs(
    outputs_path: Path,
    holdout_path: Path,
    training_path: Path,
    baseline_path: Path | None,
    output_dir: Path,
) -> dict[str, Any]:
    outputs = _load_json(outputs_path)
    holdout_hash = hashlib.sha256(holdout_path.read_bytes()).hexdigest()
    if holdout_hash != EXPECTED_HOLDOUT_SHA256:
        raise ValueError(f"Holdout hash mismatch: {holdout_hash}")

    expected_metadata = {
        "adapter_sha256": EXPECTED_ADAPTER_SHA256,
        "holdout_sha256": EXPECTED_HOLDOUT_SHA256,
        "base_model": EXPECTED_BASE_MODEL,
        "base_revision": EXPECTED_BASE_REVISION,
    }
    for field, expected in expected_metadata.items():
        if outputs.get(field) != expected:
            raise ValueError(f"Output metadata mismatch for {field}: expected {expected!r}, received {outputs.get(field)!r}.")

    holdout = load_validated_records(holdout_path, min_samples=30)
    if len(holdout) != 30:
        raise ValueError(f"Expected exactly 30 holdout records; found {len(holdout)}.")
    expected_ids = [_record_id(record) for record in holdout]
    raw_results = outputs.get("results")
    if not isinstance(raw_results, list):
        raise ValueError("Adapter output file is missing the results list.")
    results_by_id = {item.get("record_id"): item for item in raw_results if isinstance(item, dict)}
    if len(results_by_id) != len(raw_results):
        raise ValueError("Adapter output contains missing or duplicate record IDs.")
    missing_ids = [record_id for record_id in expected_ids if record_id not in results_by_id]
    unexpected_ids = sorted(set(results_by_id) - set(expected_ids))
    if missing_ids or unexpected_ids:
        raise ValueError(f"Holdout result IDs do not match. Missing={missing_ids}; unexpected={unexpected_ids}.")

    ordered_results = [results_by_id[record_id] for record_id in expected_ids]
    profile = load_candidate_profile()
    summary = summarize_results(ordered_results, profile)

    training = load_validated_records(training_path, min_samples=100)
    training_outputs = {
        _canonical(json.loads(record["messages"][2]["content"]))
        for record in training
    }
    leakage_ids = [
        result["record_id"]
        for result in ordered_results
        if isinstance(result.get("parsed"), dict) and _canonical(result["parsed"]) in training_outputs
    ]

    baseline_summary = None
    if baseline_path and baseline_path.exists():
        baseline_summary = _load_json(baseline_path).get("summary")

    gates = {
        "all_30_completed": summary["total"] == 30 and summary["request_failures"] == 0,
        "json_parse_rate_100_percent": summary["parse_rate"] == 1.0,
        "schema_valid_rate_100_percent": summary["schema_valid_rate"] == 1.0,
        "factual_and_identity_errors_zero": summary["errors"] == 0,
        "exact_training_output_leakage_zero": len(leakage_ids) == 0,
        "improves_on_recorded_baseline": (
            baseline_summary is None
            or (
                summary["errors"] < baseline_summary.get("errors", float("inf"))
                and summary["schema_valid_rate"] >= baseline_summary.get("schema_valid_rate", 0.0)
            )
        ),
    }
    report = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "artifact": expected_metadata,
        "outputs_path": str(outputs_path),
        "holdout_path": str(holdout_path),
        "training_path": str(training_path),
        "generation_options": outputs.get("generation_options"),
        "summary": summary,
        "baseline_summary": baseline_summary,
        "exact_training_output_leakage_record_ids": leakage_ids,
        "gates": gates,
        "release_gate_passed": all(gates.values()),
        "results": ordered_results,
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "resume-llama3-lora-adapter_evaluation.json"
    markdown_path = output_dir / "resume-llama3-lora-adapter_evaluation.md"
    review_path = output_dir / "resume-llama3-lora-adapter_manual_review.jsonl"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    markdown = [
        "# PEFT Adapter Holdout Evaluation",
        "",
        f"- Release gate: **{'PASS' if report['release_gate_passed'] else 'FAIL'}**",
        f"- Holdout records: {summary['total']}",
        f"- JSON parse rate: {summary['parse_rate']:.1%}",
        f"- Schema-valid rate: {summary['schema_valid_rate']:.1%}",
        f"- Factual/static errors: {summary['errors']}",
        f"- Review warnings: {summary['warnings']}",
        f"- Exact training-output leakage: {len(leakage_ids)}",
        f"- Average latency: {summary['average_latency_ms'] or 0:.0f} ms",
        "",
        "## Gates",
        "",
        *[f"- [{'x' if passed else ' '}] `{name}`" for name, passed in gates.items()],
        "",
        "## Finding counts",
        "",
        *[f"- `{code}`: {count}" for code, count in summary["finding_counts"].items()],
        "",
        "Automated gates do not replace the required manual usefulness and factual-evidence review.",
    ]
    markdown_path.write_text("\n".join(markdown), encoding="utf-8")
    with review_path.open("w", encoding="utf-8") as handle:
        for index, result in enumerate(ordered_results):
            expected = json.loads(holdout[index]["messages"][2]["content"])
            handle.write(json.dumps({
                "index": index,
                "record_id": result["record_id"],
                "expected_role": expected.get("title"),
                "expected": expected,
                "generated": result.get("parsed"),
                "raw_response": result.get("raw_response"),
                "review_decision": "",
                "review_notes": "",
            }, ensure_ascii=False) + "\n")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Score Colab PEFT adapter outputs against the untouched holdout.")
    parser.add_argument("--outputs", default="backend/finetuning/artifacts/adapter_holdout_outputs.json")
    parser.add_argument("--holdout", default="backend/data/finetuning/holdout_eval.jsonl")
    parser.add_argument("--training", default="backend/data/finetuning/training_data.jsonl")
    parser.add_argument("--baseline", default="backend/data/finetuning/reports/evaluations/llama3-latest_evaluation.json")
    parser.add_argument("--output-dir", default="backend/data/finetuning/reports/evaluations")
    args = parser.parse_args()
    try:
        report = score_adapter_outputs(
            Path(args.outputs), Path(args.holdout), Path(args.training),
            Path(args.baseline) if args.baseline else None, Path(args.output_dir),
        )
    except (ValueError, OSError, json.JSONDecodeError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2
    print(json.dumps({"summary": report["summary"], "gates": report["gates"]}, indent=2))
    return 0 if report["release_gate_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
