"""Shared domain models for RAGReady.

These models are used across ingestion, retrieval, and generation layers.
"""

import hashlib
from datetime import datetime, timezone

from pydantic import BaseModel, Field


class ChunkMetadata(BaseModel):
    """Metadata attached to each chunk for traceability."""

    source_document: str
    page_number: int | None = None
    position_in_doc: int
    chunk_index: int
    content_hash: str
    ingested_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Chunk(BaseModel):
    """A text chunk from a document with metadata."""

    chunk_id: str
    document_id: str
    text: str
    metadata: ChunkMetadata

    @classmethod
    def generate_id(cls, doc_id: str, chunk_index: int, text: str) -> str:
        """Generate a deterministic chunk ID.

        Uses SHA-256 hash of doc_id, chunk_index, and first 100 chars of text.
        This prevents inconsistent chunk IDs (Pitfall 15).
        """
        raw = f"{doc_id}:{chunk_index}:{text[:100]}"
        return hashlib.sha256(raw.encode()).hexdigest()[:16]


class Document(BaseModel):
    """Metadata for an ingested document."""

    document_id: str
    filename: str
    file_type: str
    chunk_count: int
    ingested_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    content_hash: str


class ScoredChunk(BaseModel):
    """A chunk with a retrieval score and source indicator."""

    chunk: Chunk
    score: float
    source: str  # "dense" | "sparse" | "fused"
