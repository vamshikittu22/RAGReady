"""ChromaDB storage adapter for dense (embedding-based) retrieval.

Wraps ChromaDB's PersistentClient with add, delete, and search operations.
Stores embedding model name in collection metadata for mismatch detection
(Pitfall 8).
"""

import logging
from typing import Any

import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

from ragready.core.config import Settings
from ragready.core.exceptions import IndexingError
from ragready.core.models import Chunk, ChunkMetadata, ScoredChunk

logger = logging.getLogger(__name__)


class ChromaStore:
    """Dense vector store backed by ChromaDB with persistent storage.

    Uses SentenceTransformer embeddings computed automatically at add time.
    Stores embedding model name in collection metadata for model mismatch
    detection (Pitfall 8).

    Args:
        settings: Application settings (defaults to global Settings).
    """

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or Settings()
        self._client = chromadb.PersistentClient(
            path=self._settings.chroma_persist_dir
        )
        self._embedding_fn = SentenceTransformerEmbeddingFunction(
            model_name=self._settings.embedding_model
        )
        self._collection = self._client.get_or_create_collection(
            name="ragready",
            embedding_function=self._embedding_fn,
            metadata={"embedding_model": self._settings.embedding_model},
        )

    def add_chunks(self, chunks: list[Chunk]) -> None:
        """Add chunks to the ChromaDB collection.

        Each chunk's text is automatically embedded by the configured
        SentenceTransformer model.

        Args:
            chunks: List of Chunk objects to index.

        Raises:
            IndexingError: If adding chunks fails.
        """
        if not chunks:
            return
        try:
            ids = [c.chunk_id for c in chunks]
            documents = [c.text for c in chunks]
            metadatas = [self._chunk_metadata_to_dict(c) for c in chunks]
            self._collection.add(
                ids=ids,
                documents=documents,
                metadatas=metadatas,
            )
        except Exception as exc:
            raise IndexingError(f"ChromaDB add failed: {exc}") from exc

    def delete_by_document(self, document_id: str) -> int:
        """Delete all chunks belonging to a document.

        Args:
            document_id: The document whose chunks should be deleted.

        Returns:
            Number of chunks deleted.
        """
        try:
            results = self._collection.get(
                where={"document_id": document_id},
            )
            found_ids = results["ids"]
            if not found_ids:
                return 0
            self._collection.delete(ids=found_ids)
            return len(found_ids)
        except Exception as exc:
            raise IndexingError(
                f"ChromaDB delete failed for document {document_id}: {exc}"
            ) from exc

    def search(self, query: str, k: int = 20) -> list[ScoredChunk]:
        """Search for chunks similar to the query.

        Args:
            query: The search query text.
            k: Number of results to return.

        Returns:
            List of ScoredChunk objects sorted by similarity (descending).
        """
        if self._collection.count() == 0:
            return []
        # Ensure k doesn't exceed collection size
        actual_k = min(k, self._collection.count())
        results = self._collection.query(
            query_texts=[query],
            n_results=actual_k,
            include=["documents", "metadatas", "distances"],
        )
        scored: list[ScoredChunk] = []
        ids = results["ids"][0]
        docs = results["documents"][0]
        metas = results["metadatas"][0]
        distances = results["distances"][0]

        for chunk_id, text, meta, distance in zip(ids, docs, metas, distances):
            # ChromaDB returns cosine distance; convert to similarity
            similarity = 1.0 - distance
            chunk = Chunk(
                chunk_id=chunk_id,
                document_id=meta.get("document_id", ""),
                text=text,
                metadata=ChunkMetadata(
                    source_document=meta.get("source_document", ""),
                    page_number=meta.get("page_number"),
                    position_in_doc=meta.get("position_in_doc", 0),
                    chunk_index=meta.get("chunk_index", 0),
                    content_hash=meta.get("content_hash", ""),
                    ingested_at=meta.get("ingested_at", "2000-01-01T00:00:00Z"),
                ),
            )
            scored.append(ScoredChunk(chunk=chunk, score=similarity, source="dense"))
        return scored

    def count(self) -> int:
        """Return total number of chunks in the collection."""
        return self._collection.count()

    def get_document_ids(self) -> set[str]:
        """Return unique document IDs from all stored chunks."""
        results = self._collection.get(include=["metadatas"])
        doc_ids: set[str] = set()
        if results["metadatas"]:
            for meta in results["metadatas"]:
                doc_id = meta.get("document_id")
                if doc_id:
                    doc_ids.add(doc_id)
        return doc_ids

    @staticmethod
    def _chunk_metadata_to_dict(chunk: Chunk) -> dict[str, Any]:
        """Convert a Chunk's metadata to a ChromaDB-compatible flat dict."""
        meta = chunk.metadata
        result: dict[str, Any] = {
            "document_id": chunk.document_id,
            "source_document": meta.source_document,
            "position_in_doc": meta.position_in_doc,
            "chunk_index": meta.chunk_index,
            "content_hash": meta.content_hash,
            "ingested_at": meta.ingested_at.isoformat(),
        }
        if meta.page_number is not None:
            result["page_number"] = meta.page_number
        return result
