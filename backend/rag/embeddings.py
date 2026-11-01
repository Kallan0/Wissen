"""Shared, workspace-local embedding configuration for Chroma and chunking."""

from pathlib import Path
from typing import Any

from config import settings


def get_embedding_function() -> Any:
    """Return MiniLM with its model cache in a writable project directory."""
    from chromadb.utils.embedding_functions import DefaultEmbeddingFunction, ONNXMiniLM_L6_V2

    model_dir = Path(settings.CHROMA_EMBEDDING_CACHE_DIR) / ONNXMiniLM_L6_V2.MODEL_NAME
    model_dir.mkdir(parents=True, exist_ok=True)
    # Existing Chroma collections persist the function name ``default``. Keep
    # that contract while redirecting the delegated ONNX model cache.
    ONNXMiniLM_L6_V2.DOWNLOAD_PATH = model_dir
    return DefaultEmbeddingFunction()
