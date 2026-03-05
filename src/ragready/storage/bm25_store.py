"""BM25 sparse retrieval store with disk persistence.

Uses rank_bm25.BM25Okapi for scoring and persists the chunk list to
disk via pickle, surviving restarts.
"""

import logging
import pickle
from pathlib import Path

from rank_bm25 import BM25Okapi

from ragready.core.config import Settings
from ragready.core.exceptions import IndexingError
from ragready.core.models import Chunk, ScoredChunk

logger = logging.getLogger(__name__)


class BM25Store:
    """Sparse retrieval store backed by BM25Okapi.

    Maintains an in-memory BM25 index that is rebuilt after every mutation
    (BM25Okapi cannot be incrementally updated). Persists the chunk list to
    a pickle file for crash recovery.

    Args:
        settings: Application settings (defaults to global Settings).
    """

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or Settings()
        self._persist_path = Path(self._settings.bm25_persist_path)
        self._chunks: list[Chunk] = []
        self._tokenized_corpus: list[list[str]] = []
        self._bm25: BM25Okapi | None = None
        self._load()

    def add_chunks(self, chunks: list[Chunk]) -> None:
        """Add chunks to the BM25 index and persist.

        Args:
            chunks: List of Chunk objects to index.

        Raises:
            IndexingError: If adding or persisting fails.
        """
        if not chunks:
            return
        try:
            self._chunks.extend(chunks)
            self._rebuild_index()
            self._save()
        except Exception as exc:
            raise IndexingError(f"BM25 add failed: {exc}") from exc

    def delete_by_document(self, document_id: str) -> int:
        """Delete all chunks belonging to a document.

        Args:
            document_id: The document whose chunks should be deleted.

        Returns:
            Number of chunks deleted.
        """
        original_count = len(self._chunks)
        self._chunks = [c for c in self._chunks if c.document_id != document_id]
        deleted = original_count - len(self._chunks)
        if deleted > 0:
            self._rebuild_index()
            self._save()
        return deleted

    def search(self, query: str, k: int = 20) -> list[ScoredChunk]:
        """Search for chunks matching the query using BM25 scoring.

        Args:
            query: The search query text.
            k: Number of results to return.

        Returns:
            List of ScoredChunk objects sorted by BM25 score (descending).
        """
        if not self._bm25 or not self._chunks:
            return []

        tokenized_query = self._tokenize(query)
        scores = self._bm25.get_scores(tokenized_query)

        # Get top-k indices sorted by score descending
        scored_indices = sorted(
            range(len(scores)), key=lambda i: scores[i], reverse=True
        )[:k]

        results: list[ScoredChunk] = []
        for idx in scored_indices:
            if scores[idx] <= 0:
                continue  # skip zero-score results
            results.append(
                ScoredChunk(
                    chunk=self._chunks[idx],
                    score=float(scores[idx]),
                    source="sparse",
                )
            )
        return results

    def count(self) -> int:
        """Return total number of chunks in the index."""
        return len(self._chunks)

    def get_document_ids(self) -> set[str]:
        """Return unique document IDs from all stored chunks."""
        return {c.document_id for c in self._chunks}

    def _rebuild_index(self) -> None:
        """Rebuild the BM25 index from the current chunk list."""
        self._tokenized_corpus = [self._tokenize(c.text) for c in self._chunks]
        if self._tokenized_corpus:
            self._bm25 = BM25Okapi(self._tokenized_corpus)
        else:
            self._bm25 = None

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        """Simple whitespace tokenization with lowercasing."""
        return text.lower().split()

    def _save(self) -> None:
        """Persist the chunk list to disk via pickle."""
        try:
            self._persist_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self._persist_path, "wb") as f:
                pickle.dump(self._chunks, f)
            logger.debug("BM25 index saved to %s (%d chunks)", self._persist_path, len(self._chunks))
        except Exception as exc:
            logger.error("Failed to persist BM25 index: %s", exc)
            raise IndexingError(f"BM25 persistence failed: {exc}") from exc

    def _load(self) -> None:
        """Load the chunk list from disk if it exists."""
        if not self._persist_path.exists():
            logger.debug("No BM25 index at %s — starting fresh", self._persist_path)
            return
        try:
            with open(self._persist_path, "rb") as f:
                self._chunks = pickle.load(f)
            self._rebuild_index()
            logger.info("BM25 index loaded from %s (%d chunks)", self._persist_path, len(self._chunks))
        except Exception as exc:
            logger.warning(
                "Corrupted BM25 index at %s — starting fresh: %s",
                self._persist_path,
                exc,
            )
            self._chunks = []
            self._tokenized_corpus = []
            self._bm25 = None
