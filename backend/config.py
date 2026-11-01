import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent


def _load_local_env(path: Path) -> None:
    """Load simple KEY=VALUE entries while preserving real process variables."""
    if not path.is_file():
        return
    for raw_line in path.read_text(encoding="utf-8-sig").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key.replace("_", "").isalnum():
            os.environ.setdefault(key, value)


_load_local_env(ROOT_DIR / ".env")

DATA_DIR = BASE_DIR / "data"
CHROMA_DIR = Path(os.getenv("CHROMA_DIR", str(DATA_DIR / "chroma_db"))).expanduser().resolve()
CHROMA_EMBEDDING_CACHE_DIR = Path(
    os.getenv("CHROMA_EMBEDDING_CACHE_DIR", str(DATA_DIR / "embedding_cache" / "onnx_models"))
).expanduser().resolve()
SAMPLE_DIR = Path(os.getenv("SAMPLE_DIR", str(BASE_DIR / "sample_data"))).expanduser().resolve()

DATA_DIR.mkdir(parents=True, exist_ok=True)
CHROMA_DIR.mkdir(parents=True, exist_ok=True)
CHROMA_EMBEDDING_CACHE_DIR.mkdir(parents=True, exist_ok=True)
SAMPLE_DIR.mkdir(parents=True, exist_ok=True)

class Settings:
    BASE_DIR: Path = BASE_DIR
    DATA_DIR: Path = DATA_DIR
    CHROMA_DIR: Path = CHROMA_DIR
    CHROMA_EMBEDDING_CACHE_DIR: Path = CHROMA_EMBEDDING_CACHE_DIR
    SAMPLE_DIR: Path = SAMPLE_DIR
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_DEFAULT_MODEL: str = os.getenv("OLLAMA_DEFAULT_MODEL", "llama3")
    OLLAMA_ENABLED: bool = os.getenv("OLLAMA_ENABLED", "true").strip().lower() not in {"0", "false", "no", "off"}
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "").strip()
    GROQ_BASE_URL: str = os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1").rstrip("/")
    GROQ_DEFAULT_MODEL: str = os.getenv("GROQ_DEFAULT_MODEL", "openai/gpt-oss-20b")
    GROQ_MODELS: tuple[str, ...] = tuple(
        item.strip()
        for item in os.getenv("GROQ_MODELS", "openai/gpt-oss-20b").split(",")
        if item.strip()
    )
    AI_DEFAULT_PROVIDER: str = os.getenv("AI_DEFAULT_PROVIDER", "ollama").strip().lower()
    AI_MAX_OUTPUT_TOKENS: int = int(os.getenv("AI_MAX_OUTPUT_TOKENS", "6000"))
    AI_PROVIDER_FAILURE_COOLDOWN_SECONDS: float = float(os.getenv("AI_PROVIDER_FAILURE_COOLDOWN_SECONDS", "30"))
    RAG_MAX_CONTEXT_CHARS: int = int(os.getenv("RAG_MAX_CONTEXT_CHARS", "24000"))
    SEMANTIC_CHUNK_MIN_WORDS: int = int(os.getenv("SEMANTIC_CHUNK_MIN_WORDS", "60"))
    SEMANTIC_CHUNK_MAX_WORDS: int = int(os.getenv("SEMANTIC_CHUNK_MAX_WORDS", "220"))
    SEMANTIC_CHUNK_BREAK_PERCENTILE: float = float(os.getenv("SEMANTIC_CHUNK_BREAK_PERCENTILE", "25"))
    HYBRID_DENSE_WEIGHT: float = float(os.getenv("HYBRID_DENSE_WEIGHT", "0.70"))
    HYBRID_BM25_WEIGHT: float = float(os.getenv("HYBRID_BM25_WEIGHT", "0.30"))
    HYBRID_MIN_SCORE: float = float(os.getenv("HYBRID_MIN_SCORE", "0.0"))
    COLLECTION_NAME: str = "resume_knowledge_base"

settings = Settings()
