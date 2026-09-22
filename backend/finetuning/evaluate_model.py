"""Run an Ollama model against the untouched holdout set and score outputs."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx

CURRENT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = CURRENT_DIR.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from ai.generator import extract_json  # noqa: E402
from config import settings  # noqa: E402
from finetuning.audit_dataset import AuditFinding, _audit_record, _profile_evidence_text  # noqa: E402
from finetuning.dataset_generator import load_candidate_profile  # noqa: E402
from finetuning.finetune_llama3 import REQUIRED_RESUME_KEYS, load_validated_records  # noqa: E402


def _record_id(record: dict[str, Any]) -> str:
    raw = json.dumps(record["messages"][:2], sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:16]


def summarize_results(results: list[dict[str, Any]], profile: dict[str, Any]) -> dict[str, Any]:
    findings: list[AuditFinding] = []
    parsed_count = schema_count = 0
    request_failures = 0
    failed_records = 0
    latencies: list[float] = []
    evidence = _profile_evidence_text(profile)
    for index, result in enumerate(results):
        request_failed = bool(result.get("request_error"))
        if request_failed:
            request_failures += 1
        if isinstance(result.get("latency_ms"), (int, float)):
            latencies.append(float(result["latency_ms"]))
        payload = result.get("parsed")
        if not isinstance(payload, dict):
            failed_records += 1
            continue
        parsed_count += 1
        if REQUIRED_RESUME_KEYS <= payload.keys():
            schema_count += 1
        else:
            findings.append(AuditFinding("error", "schema.missing_fields", "evaluation", index, "root", "Required resume fields are missing."))
        _audit_record(payload, dataset="evaluation", record_index=index, profile=profile, evidence_text=evidence, findings=findings)
    total = len(results)
    validation_errors = sum(item.severity == "error" for item in findings)
    errors = validation_errors + failed_records
    warnings = sum(item.severity == "warning" for item in findings)
    return {
        "total": total,
        "parsed": parsed_count,
        "parse_rate": parsed_count / total if total else 0.0,
        "request_failures": request_failures,
        "failed_records": failed_records,
        "schema_valid": schema_count,
        "schema_valid_rate": schema_count / total if total else 0.0,
        "errors": errors,
        "validation_errors": validation_errors,
        "warnings": warnings,
        "average_latency_ms": sum(latencies) / len(latencies) if latencies else None,
        "finding_counts": {
            code: sum(item.code == code for item in findings)
            for code in sorted({item.code for item in findings})
        },
    }


def evaluate_model(model: str, holdout: Path, output_dir: Path, workers: int = 2) -> dict[str, Any]:
    if not 1 <= workers <= 4:
        raise ValueError("workers must be between 1 and 4.")
    records = load_validated_records(holdout, min_samples=2)
    profile = load_candidate_profile()

    def run_one(index: int, record: dict[str, Any]) -> tuple[int, dict[str, Any]]:
        system = record["messages"][0]["content"]
        user = record["messages"][1]["content"]
        started = time.perf_counter()
        try:
            with httpx.Client(timeout=httpx.Timeout(180.0)) as client:
                response = client.post(
                    f"{settings.OLLAMA_BASE_URL.rstrip('/')}/api/generate",
                    json={
                        "model": model,
                        "prompt": f"{system}\n\n{user}",
                        "stream": False,
                        "format": "json",
                        "options": {"temperature": 0.15, "top_p": 0.9, "seed": 42, "num_predict": 1800},
                    },
                )
                response.raise_for_status()
                raw = response.json().get("response", "")
                error = None
        except Exception as exc:
            raw, error = "", str(exc)
        expected = json.loads(record["messages"][2]["content"])
        return index, {
            "record_id": _record_id(record),
            "expected_role": expected.get("title"),
            "latency_ms": round((time.perf_counter() - started) * 1000, 2),
            "raw_response": raw,
            "parsed": extract_json(raw) if raw else None,
            "request_error": error,
        }

    results_by_index: dict[int, dict[str, Any]] = {}
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = [executor.submit(run_one, index, record) for index, record in enumerate(records)]
        for completed, future in enumerate(as_completed(futures), start=1):
            index, result = future.result()
            results_by_index[index] = result
            print(f"Evaluated {completed}/{len(records)}", flush=True)
    results = [results_by_index[index] for index in range(len(records))]
    summary = summarize_results(results, profile)
    report = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "model": model,
        "holdout_path": str(holdout),
        "holdout_sha256": hashlib.sha256(holdout.read_bytes()).hexdigest(),
        "generation_options": {"temperature": 0.15, "top_p": 0.9, "seed": 42, "num_predict": 1800},
        "summary": summary,
        "results": results,
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    safe_model = model.replace(":", "-").replace("/", "-")
    json_path = output_dir / f"{safe_model}_evaluation.json"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    markdown = "\n".join([
        f"# Model Evaluation: {model}", "",
        f"- Holdout records: {summary['total']}",
        f"- JSON parse rate: {summary['parse_rate']:.1%}",
        f"- Request failures: {summary['request_failures']}",
        f"- Failed records: {summary['failed_records']}",
        f"- Schema-valid rate: {summary['schema_valid_rate']:.1%}",
        f"- Static/factual errors: {summary['errors']}",
        f"- Review warnings: {summary['warnings']}",
        f"- Average latency: {summary['average_latency_ms'] or 0:.0f} ms", "",
        "## Finding counts", "",
        *[f"- `{code}`: {count}" for code, count in summary["finding_counts"].items()], "",
    ])
    (output_dir / f"{safe_model}_evaluation.md").write_text(markdown, encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate an Ollama model on the untouched holdout set.")
    parser.add_argument("--model", required=True)
    parser.add_argument("--holdout", default="backend/data/finetuning/holdout_eval.jsonl")
    parser.add_argument("--output-dir", default="backend/data/finetuning/reports/evaluations")
    parser.add_argument("--workers", type=int, default=2)
    args = parser.parse_args()
    try:
        report = evaluate_model(args.model, Path(args.holdout), Path(args.output_dir), args.workers)
    except (ValueError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    summary = report["summary"]
    print(f"Evaluation complete: {summary['parse_rate']:.1%} parsed, {summary['errors']} errors.")
    return 1 if summary["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
