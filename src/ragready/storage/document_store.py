"""Document manifest store for tracking ingested documents.

Provides a JSON-backed manifest of all ingested documents with sync
verification across ChromaDB and BM25 stores (Pitfall 2 prevention).
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import TYPE_CHECKING

from ragready.core.models import Document

if TYPE_CHECKING:
    from ragready.storage.bm25_store import BM25Store
    from ragready.storage.chroma import ChromaStore

logger = logging.getLogger(__name__)

# Default manifest path relative to project root.
_DEFAULT_MANIFEST_PATH = "data/indexes/documents.json"


class DocumentStore:
    """Tracks ingested documents as a JSON manifest on disk.

    Provides add, get, list, and delete operations plus cross-store sync
    verification.

    Args:
        manifest_path: Path to the JSON manifest file.
    """

    def __init__(self, manifest_path: str | Path | None = None) -> None:
        self._path = Path(manifest_path or _DEFAULT_MANIFEST_PATH)
        self._documents: dict[str, Document] = {}
        self._load()

    def add_document(self, doc: Document) -> None:
        """Add a document to the manifest and persist.

        Args:
            doc: The Document to track.
        """
        self._documents[doc.document_id] = doc
        self._save()

    def get_document(self, document_id: str) -> Document | None:
        """Look up a document by ID.

        Args:
            document_id: The document's unique identifier.

        Returns:
            The Document if found, otherwise None.
        """
        return self._documents.get(document_id)

    def list_documents(self) -> list[Document]:
        """Return all tracked documents."""
        return list(self._documents.values())

    def delete_document(self, document_id: str) -> Document | None:
        """Remove a document from the manifest and persist.

        Args:
            document_id: The document to remove.

        Returns:
            The deleted Document, or None if not found.
        """
        doc = self._documents.pop(document_id, None)
        if doc is not None:
            self._save()
        return doc

    def verify_sync(
        self,
        chroma: ChromaStore,
        bm25: BM25Store,
    ) -> dict:
        """Compare document IDs across manifest, ChromaDB, and BM25.

        Returns a dict indicating whether all three stores are in sync,
        with counts and sets of missing document IDs.

        Args:
            chroma: The ChromaDB store.
            bm25: The BM25 store.

        Returns:
            Dict with keys: in_sync, manifest_count, chroma_count,
            bm25_count, missing_from_chroma, missing_from_bm25.
        """
        manifest_ids = set(self._documents.keys())
        chroma_ids = chroma.get_document_ids()
        bm25_ids = bm25.get_document_ids()

        missing_from_chroma = manifest_ids - chroma_ids
        missing_from_bm25 = manifest_ids - bm25_ids

        in_sync = (not missing_from_chroma) and (not missing_from_bm25)

        if not in_sync:
            logger.warning(
                "Index desync detected! Manifest: %d, Chroma: %d, BM25: %d. "
                "Missing from Chroma: %s, Missing from BM25: %s",
                len(manifest_ids),
                len(chroma_ids),
                len(bm25_ids),
                missing_from_chroma or "none",
                missing_from_bm25 or "none",
            )

        return {
            "in_sync": in_sync,
            "manifest_count": len(manifest_ids),
            "chroma_count": len(chroma_ids),
            "bm25_count": len(bm25_ids),
            "missing_from_chroma": missing_from_chroma,
            "missing_from_bm25": missing_from_bm25,
        }

    def _save(self) -> None:
        """Persist the manifest to disk as JSON."""
        self._path.parent.mkdir(parents=True, exist_ok=True)
        data = [doc.model_dump(mode="json") for doc in self._documents.values()]
        with open(self._path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)

    def _load(self) -> None:
        """Load the manifest from disk if it exists."""
        if not self._path.exists():
            return
        try:
            with open(self._path, encoding="utf-8") as f:
                data = json.load(f)
            for item in data:
                doc = Document.model_validate(item)
                self._documents[doc.document_id] = doc
            logger.info("Loaded %d documents from manifest", len(self._documents))
        except Exception as exc:
            logger.warning("Failed to load document manifest: %s — starting fresh", exc)
            self._documents = {}
