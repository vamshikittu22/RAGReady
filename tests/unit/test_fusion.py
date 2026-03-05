"""Unit tests for Reciprocal Rank Fusion algorithm.

Tests the RRFFusion class with known inputs and manually computed expected
outputs to verify correctness of the fusion algorithm.
"""

import pytest

from ragready.core.models import Chunk, ChunkMetadata, ScoredChunk
from ragready.retrieval.fusion import RRFFusion


def _make_chunk(chunk_id: str, text: str = "test text") -> Chunk:
    """Create a Chunk fixture with minimal required fields."""
    return Chunk(
        chunk_id=chunk_id,
        document_id="doc1",
        text=text,
        metadata=ChunkMetadata(
            source_document="test.txt",
            position_in_doc=0,
            chunk_index=0,
            content_hash="abc123",
        ),
    )


def _make_scored(chunk_id: str, score: float, source: str = "dense") -> ScoredChunk:
    """Create a ScoredChunk fixture."""
    return ScoredChunk(
        chunk=_make_chunk(chunk_id),
        score=score,
        source=source,
    )


class TestRRFFusion:
    """Tests for RRFFusion.fuse() algorithm correctness."""

    def test_overlapping_chunks_scores_are_summed(self):
        """Two lists with overlapping chunks: fused scores = sum of individual RRF scores."""
        fusion = RRFFusion(k=60)

        # List 1: A at rank 1, B at rank 2
        list1 = [
            _make_scored("A", 0.9, "dense"),
            _make_scored("B", 0.8, "dense"),
        ]
        # List 2: B at rank 1, A at rank 2
        list2 = [
            _make_scored("B", 3.5, "sparse"),
            _make_scored("A", 2.0, "sparse"),
        ]

        results = fusion.fuse([list1, list2])

        # Both A and B appear in both lists → deduplicated
        assert len(results) == 2

        # Manually compute expected RRF scores:
        # A: 1/(60+1) + 1/(60+2) = 1/61 + 1/62
        expected_a = 1.0 / 61 + 1.0 / 62
        # B: 1/(60+2) + 1/(60+1) = 1/62 + 1/61
        expected_b = 1.0 / 62 + 1.0 / 61

        # A and B have the same total score (symmetric)
        assert results[0].score == pytest.approx(expected_a, abs=1e-10)
        assert results[1].score == pytest.approx(expected_b, abs=1e-10)

        # All results should have source="fused"
        assert all(r.source == "fused" for r in results)

    def test_no_overlap_all_chunks_appear(self):
        """Two lists with NO overlap: all chunks appear with single-list RRF scores."""
        fusion = RRFFusion(k=60)

        list1 = [
            _make_scored("A", 0.9, "dense"),
            _make_scored("B", 0.8, "dense"),
        ]
        list2 = [
            _make_scored("C", 3.5, "sparse"),
            _make_scored("D", 2.0, "sparse"),
        ]

        results = fusion.fuse([list1, list2])

        # All 4 chunks should appear
        assert len(results) == 4
        result_ids = [r.chunk.chunk_id for r in results]
        assert set(result_ids) == {"A", "B", "C", "D"}

        # A and C are rank 1 in their lists: 1/(60+1)
        # B and D are rank 2 in their lists: 1/(60+2)
        expected_rank1 = 1.0 / 61
        expected_rank2 = 1.0 / 62

        scores_by_id = {r.chunk.chunk_id: r.score for r in results}
        assert scores_by_id["A"] == pytest.approx(expected_rank1, abs=1e-10)
        assert scores_by_id["C"] == pytest.approx(expected_rank1, abs=1e-10)
        assert scores_by_id["B"] == pytest.approx(expected_rank2, abs=1e-10)
        assert scores_by_id["D"] == pytest.approx(expected_rank2, abs=1e-10)

    def test_empty_input_returns_empty(self):
        """Empty list input returns empty result."""
        fusion = RRFFusion(k=60)
        assert fusion.fuse([]) == []

    def test_empty_sublists_returns_empty(self):
        """Lists of empty sublists returns empty result."""
        fusion = RRFFusion(k=60)
        assert fusion.fuse([[], []]) == []

    def test_single_list_rescores_with_rrf(self):
        """RRF of a single list re-scores items with RRF formula."""
        fusion = RRFFusion(k=60)

        single_list = [
            _make_scored("A", 0.95, "dense"),
            _make_scored("B", 0.80, "dense"),
            _make_scored("C", 0.60, "dense"),
        ]

        results = fusion.fuse([single_list])

        assert len(results) == 3

        # Scores should be RRF values, not original scores
        assert results[0].score == pytest.approx(1.0 / 61, abs=1e-10)  # rank 1
        assert results[1].score == pytest.approx(1.0 / 62, abs=1e-10)  # rank 2
        assert results[2].score == pytest.approx(1.0 / 63, abs=1e-10)  # rank 3

    def test_ordering_highest_rrf_first(self):
        """Results are sorted by RRF score descending."""
        fusion = RRFFusion(k=60)

        # C appears at rank 1 in both lists → highest fused score
        # A appears at rank 1 in list1 only
        # B appears at rank 1 in list2, rank 2 in list1
        list1 = [
            _make_scored("A", 0.9, "dense"),
            _make_scored("B", 0.8, "dense"),
            _make_scored("C", 0.7, "dense"),
        ]
        list2 = [
            _make_scored("C", 3.5, "sparse"),
            _make_scored("B", 2.0, "sparse"),
        ]

        results = fusion.fuse([list1, list2])

        # C: 1/(60+3) + 1/(60+1) = 1/63 + 1/61  (highest because rank 1 in list2)
        # B: 1/(60+2) + 1/(60+2) = 2/62
        # A: 1/(60+1) (only in list1)

        expected_c = 1.0 / 63 + 1.0 / 61
        expected_b = 1.0 / 62 + 1.0 / 62
        expected_a = 1.0 / 61

        # C should be first (highest), then B, then A
        assert results[0].chunk.chunk_id == "C"
        assert results[0].score == pytest.approx(expected_c, abs=1e-10)
        assert results[1].chunk.chunk_id == "B"
        assert results[1].score == pytest.approx(expected_b, abs=1e-10)
        assert results[2].chunk.chunk_id == "A"
        assert results[2].score == pytest.approx(expected_a, abs=1e-10)

    def test_deduplication_keeps_first_occurrence(self):
        """Deduplicated chunks keep the Chunk object from the first occurrence."""
        fusion = RRFFusion(k=60)

        chunk_a1 = Chunk(
            chunk_id="A",
            document_id="doc1",
            text="first version",
            metadata=ChunkMetadata(
                source_document="test.txt",
                position_in_doc=0,
                chunk_index=0,
                content_hash="hash1",
            ),
        )
        chunk_a2 = Chunk(
            chunk_id="A",
            document_id="doc1",
            text="second version",
            metadata=ChunkMetadata(
                source_document="test.txt",
                position_in_doc=0,
                chunk_index=0,
                content_hash="hash2",
            ),
        )

        list1 = [ScoredChunk(chunk=chunk_a1, score=0.9, source="dense")]
        list2 = [ScoredChunk(chunk=chunk_a2, score=3.5, source="sparse")]

        results = fusion.fuse([list1, list2])

        assert len(results) == 1
        assert results[0].chunk.text == "first version"

    def test_custom_k_parameter(self):
        """Different k values produce different RRF scores."""
        fusion_low_k = RRFFusion(k=10)
        fusion_high_k = RRFFusion(k=100)

        items = [_make_scored("A", 0.9, "dense")]

        result_low = fusion_low_k.fuse([items])
        result_high = fusion_high_k.fuse([items])

        # Lower k → higher score for rank 1
        # k=10: 1/(10+1) = 0.0909...
        # k=100: 1/(100+1) = 0.0099...
        assert result_low[0].score > result_high[0].score
        assert result_low[0].score == pytest.approx(1.0 / 11, abs=1e-10)
        assert result_high[0].score == pytest.approx(1.0 / 101, abs=1e-10)

    def test_three_result_lists(self):
        """RRF works with more than two result lists."""
        fusion = RRFFusion(k=60)

        list1 = [_make_scored("A", 0.9)]
        list2 = [_make_scored("A", 3.0)]
        list3 = [_make_scored("A", 0.5)]

        results = fusion.fuse([list1, list2, list3])

        assert len(results) == 1
        # A is rank 1 in all 3 lists: 3 * 1/(60+1) = 3/61
        expected = 3.0 / 61
        assert results[0].score == pytest.approx(expected, abs=1e-10)
