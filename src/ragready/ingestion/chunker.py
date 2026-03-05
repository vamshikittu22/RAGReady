"""Document chunking engine for RAGReady.

Splits extracted text into semantic chunks using LangChain's
RecursiveCharacterTextSplitter with paragraph-first separators.
"""

import logging
from datetime import datetime, timezone

from langchain_text_splitters import RecursiveCharacterTextSplitter

from ragready.core.exceptions import ChunkingError
from ragready.core.models import Chunk, ChunkMetadata
from ragready.ingestion.metadata import compute_content_hash

logger = logging.getLogger(__name__)


class DocumentChunker:
    """Splits text into overlapping chunks with rich metadata.

    Uses RecursiveCharacterTextSplitter with paragraph-first separators
    to preserve semantic boundaries (Pitfall 5 prevention).

    Args:
        chunk_size: Maximum characters per chunk (default 512).
        chunk_overlap: Overlap characters between consecutive chunks (default 50).
    """

    def __init__(self, chunk_size: int = 512, chunk_overlap: int = 50) -> None:
        if chunk_size <= 0:
            raise ChunkingError(f"chunk_size must be positive, got {chunk_size}")
        if chunk_overlap < 0:
            raise ChunkingError(f"chunk_overlap must be non-negative, got {chunk_overlap}")
        if chunk_overlap >= chunk_size:
            raise ChunkingError(
                f"chunk_overlap ({chunk_overlap}) must be less than chunk_size ({chunk_size})"
            )
        self._splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", ". ", " ", ""],
            add_start_index=True,
            strip_whitespace=True,
        )

    def chunk(
        self,
        text: str,
        document_id: str,
        source_file: str,
        page_count: int | None = None,
    ) -> list[Chunk]:
        """Split text into chunks with metadata.

        Args:
            text: The full document text to chunk.
            document_id: The unique document identifier.
            source_file: The source filename for metadata.
            page_count: Optional total page count for page number estimation.

        Returns:
            A list of Chunk objects with populated metadata.

        Raises:
            ChunkingError: If chunking fails unexpectedly.
        """
        if not text or not text.strip():
            logger.warning("Empty text provided for chunking (document_id=%s)", document_id)
            return []

        try:
            splits = self._splitter.create_documents([text])
        except Exception as exc:
            raise ChunkingError(f"Failed to chunk document {document_id}: {exc}") from exc

        total_length = len(text)
        now = datetime.now(timezone.utc)
        chunks: list[Chunk] = []

        for idx, split in enumerate(splits):
            split_text = split.page_content
            start_index = split.metadata.get("start_index", 0)

            # Estimate page number from position if page_count is available.
            page_number: int | None = None
            if page_count and total_length > 0:
                page_number = int(start_index / (total_length / page_count)) + 1
                page_number = min(page_number, page_count)

            chunk_id = Chunk.generate_id(document_id, idx, split_text)
            content_hash = compute_content_hash(split_text)

            metadata = ChunkMetadata(
                source_document=source_file,
                page_number=page_number,
                position_in_doc=start_index,
                chunk_index=idx,
                content_hash=content_hash,
                ingested_at=now,
            )

            chunks.append(
                Chunk(
                    chunk_id=chunk_id,
                    document_id=document_id,
                    text=split_text,
                    metadata=metadata,
                )
            )

        logger.debug(
            "Chunked document %s into %d chunks (source=%s)",
            document_id,
            len(chunks),
            source_file,
        )
        return chunks
