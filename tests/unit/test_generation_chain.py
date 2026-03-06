"""Unit tests for RAG generation chain and prompt building.

All tests use mocks — no real LLM API calls are made.
"""

from unittest.mock import MagicMock, PropertyMock

from ragready.core.config import Settings
from ragready.core.models import Chunk, ChunkMetadata, ScoredChunk
from ragready.generation.chain import RAGChain
from ragready.generation.models import QueryResponse, RefusalResponse
from ragready.generation.prompts import build_prompt


def _make_scored_chunk(
    text: str = "Sample chunk text",
    doc_name: str = "test.pdf",
    page: int | None = 1,
    score: float = 0.8,
    chunk_index: int = 0,
) -> ScoredChunk:
    """Helper to create a ScoredChunk for tests."""
    doc_id = "test_doc_id"
    chunk_id = Chunk.generate_id(doc_id, chunk_index, text)
    metadata = ChunkMetadata(
        source_document=doc_name,
        page_number=page,
        position_in_doc=0,
        chunk_index=chunk_index,
        content_hash="abc123",
    )
    chunk = Chunk(
        chunk_id=chunk_id,
        document_id=doc_id,
        text=text,
        metadata=metadata,
    )
    return ScoredChunk(chunk=chunk, score=score, source="fused")


class TestBuildPrompt:
    """Tests for the build_prompt function."""

    def test_build_prompt_formats_chunks(self):
        """Test build_prompt produces SystemMessage + HumanMessage with chunk formatting."""
        chunks = [
            _make_scored_chunk(text="Chunk one text", doc_name="doc1.pdf", page=1, score=0.9),
            _make_scored_chunk(
                text="Chunk two text", doc_name="doc2.md", page=None, score=0.7, chunk_index=1
            ),
        ]
        messages = build_prompt("What is the answer?", chunks)

        assert len(messages) == 2
        # SystemMessage is first
        assert "ONLY use information from the provided context" in messages[0].content
        # HumanMessage contains question and chunks
        human_msg = messages[1].content
        assert "What is the answer?" in human_msg
        assert "Chunk one text" in human_msg
        assert "Chunk two text" in human_msg

    def test_build_prompt_includes_all_chunks(self):
        """Verify all chunks appear in the formatted context."""
        chunks = [
            _make_scored_chunk(text=f"Content of chunk {i}", chunk_index=i, score=0.8 - i * 0.1)
            for i in range(5)
        ]
        messages = build_prompt("Test query", chunks)
        human_msg = messages[1].content

        for i in range(5):
            assert f"Content of chunk {i}" in human_msg
            assert f"[Chunk {i + 1}]" in human_msg

    def test_build_prompt_includes_metadata(self):
        """Verify chunk metadata (source, page, score) appears in prompt."""
        chunks = [
            _make_scored_chunk(text="Evidence text", doc_name="report.pdf", page=7, score=0.9234),
        ]
        messages = build_prompt("Query?", chunks)
        human_msg = messages[1].content

        assert "report.pdf" in human_msg
        assert "7" in human_msg
        assert "0.9234" in human_msg

    def test_build_prompt_page_na_when_none(self):
        """Verify page shows N/A when page_number is None."""
        chunks = [
            _make_scored_chunk(text="Text", doc_name="readme.md", page=None, score=0.8),
        ]
        messages = build_prompt("Q?", chunks)
        human_msg = messages[1].content
        assert "N/A" in human_msg


class TestRAGChain:
    """Tests for the RAGChain query pipeline."""

    def _make_chain(self, retriever_return=None, llm_return=None):
        """Helper to create a RAGChain with mocked retriever and LLM."""
        mock_retriever = MagicMock()
        mock_retriever.retrieve.return_value = retriever_return or []

        mock_llm = MagicMock()
        # with_structured_output returns a new mock that has invoke
        mock_structured = MagicMock()
        if llm_return is not None:
            mock_structured.invoke.return_value = llm_return
        mock_llm.with_structured_output.return_value = mock_structured

        settings = Settings()
        chain = RAGChain(retriever=mock_retriever, llm=mock_llm, settings=settings)
        return chain, mock_retriever, mock_llm, mock_structured

    def test_query_refused_no_chunks(self):
        """Mock retriever to return empty list, verify RefusalResponse returned."""
        chain, retriever, _, _ = self._make_chain(retriever_return=[])

        result = chain.query("What is the meaning of life?")

        assert isinstance(result, RefusalResponse)
        assert result.refused is True
        assert result.confidence == 0.0
        retriever.retrieve.assert_called_once_with("What is the meaning of life?")

    def test_query_refused_low_scores(self):
        """Mock retriever to return chunks with scores below threshold, verify RefusalResponse."""
        low_chunks = [
            _make_scored_chunk(text="Weak evidence", score=0.003, chunk_index=0),
            _make_scored_chunk(text="Also weak", score=0.005, chunk_index=1),
        ]
        chain, _, _, _ = self._make_chain(retriever_return=low_chunks)

        result = chain.query("Complex question?")

        assert isinstance(result, RefusalResponse)
        assert result.refused is True
        assert result.confidence == 0.005  # max of the chunk scores

    def test_query_succeeds_with_good_chunks(self):
        """Mock retriever with good chunks + mock LLM, verify QueryResponse."""
        good_chunks = [
            _make_scored_chunk(text="Strong evidence here", score=0.9, chunk_index=0),
            _make_scored_chunk(text="Supporting info", score=0.75, chunk_index=1),
        ]
        expected_response = QueryResponse(
            answer="The answer based on strong evidence.",
            citations=[],
            confidence=0.85,
        )
        chain, _, mock_llm, mock_structured = self._make_chain(
            retriever_return=good_chunks,
            llm_return=expected_response,
        )

        result = chain.query("What is the answer?")

        assert isinstance(result, QueryResponse)
        assert result.answer == "The answer based on strong evidence."
        assert result.confidence == 0.85
        mock_llm.with_structured_output.assert_called_once_with(QueryResponse)
        mock_structured.invoke.assert_called_once()

    def test_refusal_includes_max_score(self):
        """Verify the RefusalResponse.confidence equals the max chunk score."""
        chunks = [
            _make_scored_chunk(text="A", score=0.002, chunk_index=0),
            _make_scored_chunk(text="B", score=0.008, chunk_index=1),
            _make_scored_chunk(text="C", score=0.001, chunk_index=2),
        ]
        chain, _, _, _ = self._make_chain(retriever_return=chunks)

        result = chain.query("Marginal question?")

        assert isinstance(result, RefusalResponse)
        assert result.confidence == 0.008  # max score from chunks

    def test_query_calls_retriever_with_question(self):
        """Verify the retriever is called with the exact user question."""
        chain, retriever, _, _ = self._make_chain(retriever_return=[])

        chain.query("Specific user question here")

        retriever.retrieve.assert_called_once_with("Specific user question here")

    def test_chain_uses_structured_output(self):
        """Verify the chain calls with_structured_output on the LLM."""
        good_chunks = [
            _make_scored_chunk(text="Evidence", score=0.9, chunk_index=0),
        ]
        expected_response = QueryResponse(
            answer="Answer",
            citations=[],
            confidence=0.9,
        )
        chain, _, mock_llm, _ = self._make_chain(
            retriever_return=good_chunks,
            llm_return=expected_response,
        )

        chain.query("Question?")

        mock_llm.with_structured_output.assert_called_once_with(QueryResponse)
