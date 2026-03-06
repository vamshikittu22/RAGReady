"""Custom exceptions for RAGReady.

Hierarchy:
    RAGReadyError (base)
    ├── ExtractionError     — document extraction failures
    ├── ChunkingError       — chunking failures
    ├── IndexingError       — indexing failures
    ├── RetrievalError      — retrieval failures
    ├── DocumentNotFoundError — document doesn't exist
    ├── GenerationError     — LLM generation failures
    └── LLMUnavailableError — both primary and fallback LLMs unavailable
"""


class RAGReadyError(Exception):
    """Base exception for all RAGReady errors."""


class ExtractionError(RAGReadyError):
    """Raised when document text extraction fails."""


class ChunkingError(RAGReadyError):
    """Raised when document chunking fails."""


class IndexingError(RAGReadyError):
    """Raised when indexing chunks fails."""


class RetrievalError(RAGReadyError):
    """Raised when retrieval query fails."""


class DocumentNotFoundError(RAGReadyError):
    """Raised when a requested document does not exist."""


class GenerationError(RAGReadyError):
    """Raised when LLM generation fails."""


class LLMUnavailableError(RAGReadyError):
    """Raised when both primary and fallback LLMs are unavailable."""
