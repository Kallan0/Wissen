import sys
import json
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from rag.ingestion import IngestionService
from rag.vectorstore import vector_store

def main():
    sample_file = backend_dir / "sample_data" / "sample_profile.json"
    if not sample_file.exists():
        print(f"Error: Sample profile not found at {sample_file}")
        return

    print("Clearing previous vector store data...")
    vector_store.clear_all()

    print(f"Reading sample data from {sample_file}...")
    with open(sample_file, "r", encoding="utf-8") as f:
        profile_data = json.load(f)

    print("Ingesting structured profile into ChromaDB...")
    counts = IngestionService.ingest_structured_profile(profile_data)
    print("Ingestion complete! Chunks indexed:")
    for cat, count in counts.items():
        print(f" - {cat}: {count} items")

    stats = vector_store.get_stats()
    print(f"Total vector database records: {stats['total_items']}")

if __name__ == "__main__":
    main()
