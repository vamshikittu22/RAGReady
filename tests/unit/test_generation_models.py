"""Unit tests for generation Pydantic models."""

import pytest
from pydantic import ValidationError

from ragready.generation.models import Citation, QueryResponse, RefusalResponse


class TestCitation:
    """Tests for the Citation model."""

    def test_citation_valid(self):
        """Create a Citation with all fields, verify serialization."""
        citation = Citation(
            chunk_text="The quick brown fox jumps over the lazy dog.",
            document_name="animals.pdf",
            page_number=3,
            relevance_score=0.85,
        )
        assert citation.chunk_text == "The quick brown fox jumps over the lazy dog."
        assert citation.document_name == "animals.pdf"
        assert citation.page_number == 3
        assert citation.relevance_score == 0.85

    def test_citation_optional_page(self):
        """Verify page_number can be None."""
        citation = Citation(
            chunk_text="Some text",
            document_name="doc.md",
            page_number=None,
            relevance_score=0.7,
        )
        assert citation.page_number is None

    def test_citation_serialization(self):
        """Verify .model_dump() round-trips correctly."""
        citation = Citation(
            chunk_text="Test text",
            document_name="test.pdf",
            page_number=1,
            relevance_score=0.9,
        )
        data = citation.model_dump()
        assert data["chunk_text"] == "Test text"
        assert data["document_name"] == "test.pdf"
        assert data["page_number"] == 1
        assert data["relevance_score"] == 0.9


class TestQueryResponse:
    """Tests for the QueryResponse model."""

    def test_query_response_valid(self):
        """Create QueryResponse with answer, citations list, confidence."""
        citation = Citation(
            chunk_text="Evidence text",
            document_name="source.pdf",
            page_number=5,
            relevance_score=0.88,
        )
        response = QueryResponse(
            answer="The answer based on evidence.",
            citations=[citation],
            confidence=0.85,
        )
        assert response.answer == "The answer based on evidence."
        assert len(response.citations) == 1
        assert response.confidence == 0.85

    def test_query_response_confidence_bounds(self):
        """Verify confidence rejects values <0 or >1."""
        with pytest.raises(ValidationError):
            QueryResponse(
                answer="test",
                citations=[],
                confidence=-0.1,
            )
        with pytest.raises(ValidationError):
            QueryResponse(
                answer="test",
                citations=[],
                confidence=1.5,
            )

    def test_query_response_to_dict(self):
        """Verify .model_dump() produces expected JSON structure."""
        citation = Citation(
            chunk_text="chunk",
            document_name="doc.pdf",
            page_number=2,
            relevance_score=0.75,
        )
        response = QueryResponse(
            answer="Answer text",
            citations=[citation],
            confidence=0.9,
        )
        data = response.model_dump()
        assert "answer" in data
        assert "citations" in data
        assert "confidence" in data
        assert isinstance(data["citations"], list)
        assert len(data["citations"]) == 1
        assert data["citations"][0]["document_name"] == "doc.pdf"

    def test_query_response_confidence_edge_values(self):
        """Verify confidence accepts boundary values 0.0 and 1.0."""
        resp_zero = QueryResponse(answer="test", citations=[], confidence=0.0)
        assert resp_zero.confidence == 0.0

        resp_one = QueryResponse(answer="test", citations=[], confidence=1.0)
        assert resp_one.confidence == 1.0


class TestRefusalResponse:
    """Tests for the RefusalResponse model."""

    def test_refusal_response_valid(self):
        """Create RefusalResponse, verify refused=True."""
        refusal = RefusalResponse(
            reason="Insufficient evidence to answer confidently",
            confidence=0.3,
        )
        assert refusal.refused is True
        assert refusal.reason == "Insufficient evidence to answer confidently"
        assert refusal.confidence == 0.3

    def test_refusal_response_refused_defaults_true(self):
        """Verify refused defaults to True even when not explicitly set."""
        refusal = RefusalResponse(
            reason="No relevant chunks found",
            confidence=0.1,
        )
        assert refusal.refused is True

    def test_refusal_response_confidence_bounds(self):
        """Verify confidence rejects out-of-range values."""
        with pytest.raises(ValidationError):
            RefusalResponse(reason="test", confidence=-0.5)
        with pytest.raises(ValidationError):
            RefusalResponse(reason="test", confidence=2.0)
