"""Reciprocal Rank Fusion (RRF) algorithm for combining retrieval results.

Implements the RRF algorithm from Cormack et al. (2009):
  rrf_score(d) = sum(1 / (k + rank_i)) for each result list

where k is a constant (default 60) and rank_i is the 1-indexed rank of
document d in result list i.
"""

from ragready.core.models import Chunk, ScoredChunk


class RRFFusion:
    """Reciprocal Rank Fusion for combining multiple ranked result lists.

    Deduplicates results by chunk_id, keeping the first occurrence's Chunk
    data, and sums RRF scores across all input lists.

    Args:
        k: RRF constant (default: 60). Higher values reduce the impact
           of high-ranked results.
    """

    def __init__(self, k: int = 60) -> None:
        self._k = k

    def fuse(self, result_lists: list[list[ScoredChunk]]) -> list[ScoredChunk]:
        """Fuse multiple ranked result lists using RRF.

        Args:
            result_lists: List of ranked result lists (e.g., [dense_results,
                sparse_results]).

        Returns:
            Single list of ScoredChunk objects deduplicated by chunk_id,
            sorted by cumulative RRF score (descending), with source="fused".
        """
        if not result_lists:
            return []

        # Accumulate RRF scores per chunk_id
        rrf_scores: dict[str, float] = {}
        chunk_map: dict[str, Chunk] = {}

        for result_list in result_lists:
            for rank_0, scored_chunk in enumerate(result_list):
                chunk_id = scored_chunk.chunk.chunk_id
                # RRF formula: 1 / (k + rank) where rank is 1-indexed
                rank_1 = rank_0 + 1
                rrf_score = 1.0 / (self._k + rank_1)

                rrf_scores[chunk_id] = rrf_scores.get(chunk_id, 0.0) + rrf_score

                # Keep the first occurrence of each chunk
                if chunk_id not in chunk_map:
                    chunk_map[chunk_id] = scored_chunk.chunk

        # Sort by cumulative RRF score descending
        sorted_ids = sorted(rrf_scores.keys(), key=lambda cid: rrf_scores[cid], reverse=True)

        return [
            ScoredChunk(
                chunk=chunk_map[chunk_id],
                score=rrf_scores[chunk_id],
                source="fused",
            )
            for chunk_id in sorted_ids
        ]
