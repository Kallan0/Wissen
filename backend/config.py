import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
CHROMA_DIR = Path(os.getenv("CHROMA_DIR", str(DATA_DIR / "chroma_db"))).expanduser().resolve()
PDF_DIR = Path(os.getenv("PDF_DIR", str(DATA_DIR / "generated_pdfs"))).expanduser().resolve()
SAMPLE_DIR = Path(os.getenv("SAMPLE_DIR", str(BASE_DIR / "sample_data"))).expanduser().resolve()

DATA_DIR.mkdir(parents=True, exist_ok=True)
CHROMA_DIR.mkdir(parents=True, exist_ok=True)
PDF_DIR.mkdir(parents=True, exist_ok=True)
SAMPLE_DIR.mkdir(parents=True, exist_ok=True)

class Settings:
    BASE_DIR: Path = BASE_DIR
    DATA_DIR: Path = DATA_DIR
    CHROMA_DIR: Path = CHROMA_DIR
    PDF_DIR: Path = PDF_DIR
    SAMPLE_DIR: Path = SAMPLE_DIR
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_DEFAULT_MODEL: str = os.getenv("OLLAMA_DEFAULT_MODEL", "llama3")
    COLLECTION_NAME: str = "resume_knowledge_base"

settings = Settings()
