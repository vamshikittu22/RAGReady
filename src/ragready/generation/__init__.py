"""RAG generation pipeline with citation-enforced structured output.

Provides the core generation chain: query -> retrieve -> format -> generate -> validate.
Supports Gemini Flash primary LLM with automatic Qwen/Ollama fallback.
"""

from ragready.generation.llm import LLMWithFallback, create_llm
from ragready.generation.models import (
    Citation,
    QueryResponse,
    QueryResult,
    RefusalResponse,
)

__all__ = [
    "Citation",
    "LLMWithFallback",
    "QueryResponse",
    "QueryResult",
    "RefusalResponse",
    "create_llm",
]
