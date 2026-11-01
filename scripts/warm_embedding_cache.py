"""Download and validate the project-local Chroma MiniLM embedding cache."""

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from rag.embeddings import get_embedding_function  # noqa: E402


def main() -> None:
    embeddings = get_embedding_function()(["Verify the local resume embedding cache."])
    if len(embeddings) != 1 or len(embeddings[0]) == 0:
        raise RuntimeError("Embedding cache warm-up returned no vector.")
    print(f"Embedding cache ready: {len(embeddings[0])} dimensions")


if __name__ == "__main__":
    main()
