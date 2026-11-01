"""Rebuild legacy raw-document chunks using the current logical-unit chunker."""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))

from rag.ingestion import IngestionService, semantic_chunk_text  # noqa: E402
from rag.vectorstore import vector_store  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="Write rebuilt chunks to ChromaDB")
    args = parser.parse_args()

    items = vector_store.get_all_items().get("raw_documents", [])
    grouped: dict[str, list[dict]] = defaultdict(list)
    for item in items:
        title = str((item.get("metadata") or {}).get("title") or "Document")
        grouped[title].append(item)

    plan = []
    for title, source_items in grouped.items():
        ordered = sorted(
            source_items,
            key=lambda item: int((item.get("metadata") or {}).get("chunk_index", 0)),
        )
        recovered_text = "\n".join(
            str(item.get("document") or "").strip() for item in ordered
        ).strip()
        rebuilt = semantic_chunk_text(recovered_text)
        plan.append({"title": title, "before": len(ordered), "after": len(rebuilt), "text": recovered_text})
        print(f"{title}: {len(ordered)} legacy chunks -> {len(rebuilt)} logical sections")

    if not args.apply:
        print("Dry run only. Pass --apply to update ChromaDB.")
        return 0

    backup_dir = BACKEND / "data" / "reindex_backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    backup_path = backup_dir / f"raw_documents_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    backup_path.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")

    for entry in plan:
        IngestionService.ingest_text(entry["text"], entry["title"], tags=["resume", "reindexed"])
    print(f"Backup: {backup_path}")
    print(f"Indexed {sum(entry['after'] for entry in plan)} logical sections.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
