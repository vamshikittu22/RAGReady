"""Hybrid retriever orchestrating dense + sparse search with RRF fusion.

Combines DenseRetriever (ChromaDB) and SparseRetriever (BM25) results
using Reciprocal Rank Fusion, returning the top-k most relevant chunks.
"""

from ragready.core.config import Settings
from ragready.core.models import ScoredChunk
from ragready.retrieval.dense import DenseRetriever
from ragready.retrieval.fusion import RRFFusion
from ragready.retrieval.sparse import SparseRetriever
from ragready.storage.bm25_store import BM25Store
from ragready.storage.chroma import ChromaStore


class HybridRetriever:
    """Orchestrates hybrid retrieval: dense + sparse → RRF fusion → top-k.

    Queries both ChromaDB (semantic similarity) and BM25 (keyword matching),
    fuses results with Reciprocal Rank Fusion, and returns the top-k chunks.

    NOTE: Cross-encoder reranking is deferred to v2 per roadmap decision.
    The pipeline is: dense + sparse → RRF → top-k. The architecture supports
    adding a reranker step later without structural changes.

    Args:
        dense: Dense retriever (ChromaDB).
        sparse: Sparse retriever (BM25).
        fusion: RRF fusion instance.
        top_k: Number of final results to return (default: 5).
    """

    def __init__(
        self,
        dense: DenseRetriever,
        sparse: SparseRetriever,
        fusion: RRFFusion,
        top_k: int = 5,
    ) -> None:
        self._dense = dense
        self._sparse = sparse
        self._fusion = fusion
        self._top_k = top_k

    def retrieve(self, query: str) -> list[ScoredChunk]:
        """Retrieve the top-k most relevant chunks for a query.

        Performs hybrid retrieval by:
        1. Dense search (ChromaDB embedding similarity)
        2. Sparse search (BM25 keyword matching)
        3. RRF fusion (combine and deduplicate)
        4. Truncate to top-k

        Args:
            query: The search query text.

        Returns:
            List of up to top_k ScoredChunk objects with source="fused",
            sorted by cumulative RRF score (descending).
        """
        # Stage 1: Retrieve from both sources
        dense_results = self._dense.retrieve(query)
        sparse_results = self._sparse.retrieve(query)

        # Stage 2: Fuse results with RRF
        fused = self._fusion.fuse([dense_results, sparse_results])

        # Stage 3: Truncate to top-k
        return fused[: self._top_k]


def create_retriever(
    chroma: ChromaStore,
    bm25: BM25Store,
    settings: Settings | None = None,
) -> HybridRetriever:
    """Factory: construct a fully-wired HybridRetriever from stores and settings.

    Args:
        chroma: ChromaDB store for dense retrieval.
        bm25: BM25 store for sparse retrieval.
        settings: Optional Settings override (uses defaults if None).

    Returns:
        A ready-to-use HybridRetriever.
    """
    settings = settings or Settings()
    dense = DenseRetriever(chroma=chroma, top_k=settings.dense_top_k)
    sparse = SparseRetriever(bm25=bm25, top_k=settings.sparse_top_k)
    fusion = RRFFusion(k=settings.rrf_k)
    return HybridRetriever(
        dense=dense,
        sparse=sparse,
        fusion=fusion,
        top_k=settings.final_top_k,
    )
