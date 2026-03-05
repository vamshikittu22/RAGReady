"""Ingestion pipeline: extract → chunk → dual-index.

Orchestrates the full document ingestion flow, ensuring chunks are indexed
atomically in both ChromaDB (dense) and BM25 (sparse) stores.
"""

import logging
from pathlib import Path

from ragready.core.config import Settings
from ragready.core.exceptions import IndexingError
from ragready.core.models import Document
from ragready.ingestion.chunker import DocumentChunker
from ragready.ingestion.extractors import create_default_registry
from ragready.ingestion.extractors.base import ExtractorRegistry
from ragready.ingestion.metadata import (
    compute_content_hash,
    compute_document_id,
    detect_file_type,
)
from ragready.storage.bm25_store import BM25Store
from ragready.storage.chroma import ChromaStore
from ragready.storage.document_store import DocumentStore

logger = logging.getLogger(__name__)


class IngestionPipeline:
    """Orchestrates document ingestion: extract → chunk → dual-index.

    Ensures atomic dual-indexing — if one store fails, the other is
    cleaned up to prevent index desync (Pitfall 2).

    Args:
        extractor_registry: Registry of document extractors.
        chunker: Document chunking engine.
        chroma: ChromaDB dense store.
        bm25: BM25 sparse store.
        doc_store: Document manifest store.
    """

    def __init__(
        self,
        extractor_registry: ExtractorRegistry,
        chunker: DocumentChunker,
        chroma: ChromaStore,
        bm25: BM25Store,
        doc_store: DocumentStore,
    ) -> None:
        self._registry = extractor_registry
        self._chunker = chunker
        self._chroma = chroma
        self._bm25 = bm25
        self._doc_store = doc_store

    @property
    def chroma(self) -> ChromaStore:
        """Public accessor for the ChromaDB store (used by retrieval layer)."""
        return self._chroma

    @property
    def bm25(self) -> BM25Store:
        """Public accessor for the BM25 store (used by retrieval layer)."""
        return self._bm25

    @property
    def doc_store(self) -> DocumentStore:
        """Public accessor for the document manifest store."""
        return self._doc_store

    def list_documents(self) -> list[Document]:
        """List all ingested documents.

        Returns:
            List of Document records.
        """
        return self._doc_store.list_documents()

    def ingest(self, file_path: Path) -> Document:
        """Ingest a document: extract text, chunk, and dual-index.

        Args:
            file_path: Path to the document file.

        Returns:
            A Document record describing the ingested file.

        Raises:
            FileNotFoundError: If the file does not exist.
            ExtractionError: If text extraction fails.
            ChunkingError: If chunking fails.
            IndexingError: If indexing to either store fails.
        """
        # 1. Validate file exists
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        # 2. Extract text
        extracted = self._registry.extract(file_path)

        # 3. Compute document ID
        content_hash = compute_content_hash(extracted.text)
        document_id = compute_document_id(file_path.name, content_hash)

        # 4. Check for duplicate
        existing = self._doc_store.get_document(document_id)
        if existing is not None:
            logger.info(
                "Document already ingested: %s (id=%s)", file_path.name, document_id
            )
            return existing

        # 5. Detect file type and chunk text
        file_type = detect_file_type(file_path)
        page_count = extracted.metadata.get("page_count")
        chunks = self._chunker.chunk(
            text=extracted.text,
            document_id=document_id,
            source_file=file_path.name,
            page_count=page_count,
        )

        # 6. Index to ChromaDB
        self._chroma.add_chunks(chunks)

        # 7. Index to BM25 (with cleanup on failure)
        try:
            self._bm25.add_chunks(chunks)
        except Exception as exc:
            # Cleanup ChromaDB to prevent desync (Pitfall 2)
            logger.error(
                "BM25 indexing failed for %s — cleaning up ChromaDB: %s",
                file_path.name,
                exc,
            )
            try:
                self._chroma.delete_by_document(document_id)
            except Exception as cleanup_exc:
                logger.error("ChromaDB cleanup also failed: %s", cleanup_exc)
            raise IndexingError(
                f"BM25 indexing failed for {file_path.name}: {exc}"
            ) from exc

        # 8. Create Document record
        doc = Document(
            document_id=document_id,
            filename=file_path.name,
            file_type=file_type,
            chunk_count=len(chunks),
            content_hash=content_hash,
        )
        self._doc_store.add_document(doc)

        # 9. Log result
        logger.info(
            "%s: %d chunks indexed (id=%s)",
            file_path.name,
            len(chunks),
            document_id,
        )
        return doc

    def delete(self, document_id: str) -> bool:
        """Delete a document from all stores.

        Args:
            document_id: The document ID to delete.

        Returns:
            True if the document was found and deleted, False otherwise.
        """
        doc = self._doc_store.delete_document(document_id)
        if doc is None:
            return False

        chroma_count = self._chroma.delete_by_document(document_id)
        bm25_count = self._bm25.delete_by_document(document_id)
        logger.info(
            "Deleted document %s: %d chroma chunks, %d bm25 chunks",
            document_id,
            chroma_count,
            bm25_count,
        )
        return True


def create_pipeline(settings: Settings | None = None) -> IngestionPipeline:
    """Factory: construct a fully-wired IngestionPipeline from Settings.

    Args:
        settings: Optional Settings override (uses defaults if None).

    Returns:
        A ready-to-use IngestionPipeline.
    """
    settings = settings or Settings()
    registry = create_default_registry()
    chunker = DocumentChunker(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
    )
    chroma = ChromaStore(settings=settings)
    bm25 = BM25Store(settings=settings)
    doc_store = DocumentStore()
    return IngestionPipeline(
        extractor_registry=registry,
        chunker=chunker,
        chroma=chroma,
        bm25=bm25,
        doc_store=doc_store,
    )
