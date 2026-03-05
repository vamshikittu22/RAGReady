"""Dense retriever wrapping ChromaDB similarity search.

Queries ChromaDB for semantically similar chunks using embedding-based
cosine similarity.
"""

from ragready.core.models import ScoredChunk
from ragready.storage.chroma import ChromaStore


class DenseRetriever:
    """Dense retriever using ChromaDB vector search.

    Wraps ChromaStore.search() with a configurable top-k parameter.

    Args:
        chroma: The ChromaDB store to search.
        top_k: Number of results to retrieve (default: 20).
    """

    def __init__(self, chroma: ChromaStore, top_k: int = 20) -> None:
        self._chroma = chroma
        self._top_k = top_k

    def retrieve(self, query: str) -> list[ScoredChunk]:
        """Retrieve chunks similar to the query via dense embedding search.

        Args:
            query: The search query text.

        Returns:
            List of ScoredChunk objects with source="dense", sorted by
            cosine similarity (descending).
        """
        return self._chroma.search(query, k=self._top_k)
