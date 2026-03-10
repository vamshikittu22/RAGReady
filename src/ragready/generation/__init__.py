"""RAG generation pipeline with citation-enforced structured output.

Provides the core generation chain: query -> retrieve -> format -> generate -> validate.
Supports Gemini Flash primary LLM with automatic Qwen/Ollama fallback.
"""

from ragready.generation.chain import RAGChain, create_rag_chain
from ragready.generation.llm import LLMWrapper, create_llm
from ragready.generation.models import (
    Citation,
    QueryResponse,
    QueryResult,
    RefusalResponse,
)

__all__ = [
    "Citation",
    "LLMWrapper",
    "QueryResponse",
    "QueryResult",
    "RAGChain",
    "RefusalResponse",
    "create_llm",
    "create_rag_chain",
]
