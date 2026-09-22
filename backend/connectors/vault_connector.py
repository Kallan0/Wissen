import os
import logging
from pathlib import Path
from typing import Dict, Any
from rag.ingestion import IngestionService
from rag.vectorstore import vector_store

logger = logging.getLogger("resume_builder.vault_connector")


class VaultConnector:
    """
    Recursively scans a local folder path (Obsidian vault, Notion export, or Markdown notes directory),
    reading markdown/text notes and embedding them into ChromaDB.
    """

    @classmethod
    def scan_and_ingest_vault(
        self,
        directory_path: str,
        category: str = "markdown_vault"
    ) -> Dict[str, Any]:
        path = Path(directory_path).resolve()
        if not path.exists() or not path.is_dir():
            raise ValueError(f"Directory path does not exist or is not a folder: {directory_path}")

        files_scanned = 0
        total_chunks = 0
        processed_files = []

        # Supported extensions
        allowed_exts = {".md", ".markdown", ".txt", ".org"}

        for root, _, files in os.walk(path):
            # Skip hidden folders (.obsidian, .git, node_modules)
            if any(part.startswith(".") or part in ["node_modules", "venv", "__pycache__"] for part in Path(root).parts):
                continue

            for file in files:
                file_path = Path(root) / file
                if file_path.suffix.lower() in allowed_exts:
                    try:
                        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                            content = f.read()

                        if len(content.strip()) < 20:
                            continue

                        title = file_path.stem.replace("-", " ").replace("_", " ").title()
                        chunks = IngestionService.ingest_text(
                            content=content,
                            title=title,
                            category=category,
                            tags=["vault", file_path.suffix.lower().strip(".")]
                        )
                        files_scanned += 1
                        total_chunks += chunks
                        processed_files.append({"title": title, "path": str(file_path), "chunks": chunks})
                    except Exception as e:
                        logger.warning("Could not read vault note %s: %s", file_path, e)

        stats = vector_store.get_stats()
        return {
            "status": "success",
            "vault_path": str(path),
            "files_scanned": files_scanned,
            "total_chunks": total_chunks,
            "processed_files": processed_files[:20],  # Return preview of first 20 notes
            "stats": stats
        }


vault_connector = VaultConnector()
