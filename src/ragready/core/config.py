"""RAGReady configuration via Pydantic Settings.

All configuration is loaded from environment variables with the RAGREADY_ prefix.
Defaults are sensible for local development.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables.

    All env vars are prefixed with RAGREADY_ (e.g., RAGREADY_CHUNK_SIZE=512).
    A .env file in the project root is also loaded if present.
    """

    model_config = SettingsConfigDict(env_prefix="RAGREADY_", env_file=".env")

    # API Keys
    google_api_key: str = ""

    # Embedding
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"

    # Chunking
    chunk_size: int = 512
    chunk_overlap: int = 50

    # Retrieval
    dense_top_k: int = 20
    sparse_top_k: int = 20
    rrf_k: int = 60
    final_top_k: int = 5

    # Generation
    confidence_threshold: float = 0.6
    temperature: float = 0.1

    # LLM
    llm_model: str = "gemini-2.0-flash"
    llm_max_retries: int = 2
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen2.5:7b"

    # Observability
    phoenix_endpoint: str = "http://localhost:6006/v1/traces"
    phoenix_enabled: bool = False

    # Storage
    chroma_persist_dir: str = "./data/indexes/chroma"
    bm25_persist_path: str = "./data/indexes/bm25_index.pkl"
