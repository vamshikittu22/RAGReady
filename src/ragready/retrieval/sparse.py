"""Sparse retriever wrapping BM25 keyword search.

Queries the BM25 index for chunks matching query terms by keyword
frequency scoring.
"""

from ragready.core.models import ScoredChunk
from ragready.storage.bm25_store import BM25Store


class SparseRetriever:
    """Sparse retriever using BM25Okapi keyword matching.

    Wraps BM25Store.search() with a configurable top-k parameter.

    Args:
        bm25: The BM25 store to search.
        top_k: Number of results to retrieve (default: 20).
    """

    def __init__(self, bm25: BM25Store, top_k: int = 20) -> None:
        self._bm25 = bm25
        self._top_k = top_k

    def retrieve(self, query: str) -> list[ScoredChunk]:
        """Retrieve chunks matching the query via BM25 keyword scoring.

        Args:
            query: The search query text.

        Returns:
            List of ScoredChunk objects with source="sparse", sorted by
            BM25 score (descending).
        """
        return self._bm25.search(query, k=self._top_k)
