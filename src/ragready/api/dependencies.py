"""FastAPI dependency injection for RAGReady.

Uses @lru_cache to create singletons for Settings, IngestionPipeline,
and RAGChain, ensuring consistent state across requests.
"""

from functools import lru_cache

from ragready.core.config import Settings
from ragready.generation.chain import RAGChain, create_rag_chain
from ragready.ingestion.pipeline import IngestionPipeline, create_pipeline
from ragready.retrieval.hybrid import create_retriever


@lru_cache
def get_settings() -> Settings:
    """Get application settings (singleton)."""
    return Settings()


@lru_cache
def get_pipeline() -> IngestionPipeline:
    """Get the ingestion pipeline (singleton)."""
    settings = get_settings()
    return create_pipeline(settings)


@lru_cache
def get_rag_chain() -> RAGChain:
    """Get the RAG chain (singleton).

    Wires: Settings -> Pipeline -> Retriever -> RAGChain.
    """
    settings = get_settings()
    pipeline = get_pipeline()
    retriever = create_retriever(
        chroma=pipeline.chroma,
        bm25=pipeline.bm25,
        settings=settings,
    )
    return create_rag_chain(retriever=retriever, settings=settings)
