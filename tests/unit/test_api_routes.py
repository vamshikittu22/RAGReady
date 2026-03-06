"""Tests for RAGReady API routes.

Uses FastAPI's TestClient with dependency overrides to mock
the pipeline and RAG chain, avoiding real LLM calls and storage.
"""

from io import BytesIO
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from ragready.api.app import create_app
from ragready.api.dependencies import get_pipeline, get_rag_chain, get_settings
from ragready.core.config import Settings
from ragready.core.models import Document
from ragready.generation.models import (
    Citation,
    QueryResponse,
    RefusalResponse,
)


def _mock_settings() -> Settings:
    """Create Settings with test defaults (no real API keys needed)."""
    return Settings(
        google_api_key="test-key",
        phoenix_enabled=False,
    )


def _create_test_client(
    mock_pipeline=None, mock_chain=None, mock_settings_obj=None
) -> TestClient:
    """Create a TestClient with dependency overrides."""
    app = create_app()
    app.dependency_overrides[get_settings] = lambda: (
        mock_settings_obj or _mock_settings()
    )
    if mock_pipeline is not None:
        app.dependency_overrides[get_pipeline] = lambda: mock_pipeline
    if mock_chain is not None:
        app.dependency_overrides[get_rag_chain] = lambda: mock_chain
    return TestClient(app)


class TestHealthEndpoint:
    """Tests for GET /health."""

    def test_health_returns_200(self):
        """GET /health returns 200 with expected fields."""
        mock_pipeline = MagicMock()
        mock_pipeline.list_documents.return_value = []

        client = _create_test_client(mock_pipeline=mock_pipeline)
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["version"] == "0.1.0"
        assert "llm_model" in data
        assert "document_count" in data
        assert data["document_count"] == 0
        assert "phoenix_enabled" in data


class TestQueryEndpoint:
    """Tests for POST /query."""

    def test_query_returns_answer(self):
        """POST /query with mocked RAGChain returning QueryResponse."""
        mock_chain = MagicMock()
        mock_chain.query.return_value = QueryResponse(
            answer="Test answer based on evidence.",
            citations=[
                Citation(
                    chunk_text="relevant text",
                    document_name="doc.pdf",
                    page_number=1,
                    relevance_score=0.85,
                )
            ],
            confidence=0.9,
        )

        client = _create_test_client(mock_chain=mock_chain)
        response = client.post("/query", json={"question": "What is RAG?"})

        assert response.status_code == 200
        data = response.json()
        assert "answer" in data
        assert data["answer"] == "Test answer based on evidence."
        assert len(data["citations"]) == 1
        assert data["confidence"] == 0.9

    def test_query_returns_refusal(self):
        """POST /query with mocked RAGChain returning RefusalResponse."""
        mock_chain = MagicMock()
        mock_chain.query.return_value = RefusalResponse(
            reason="No relevant documents found",
            confidence=0.2,
        )

        client = _create_test_client(mock_chain=mock_chain)
        response = client.post("/query", json={"question": "Unknown topic?"})

        assert response.status_code == 200
        data = response.json()
        assert data["refused"] is True
        assert "reason" in data

    def test_query_empty_question_returns_422(self):
        """POST /query with empty question returns 422 validation error."""
        mock_chain = MagicMock()
        client = _create_test_client(mock_chain=mock_chain)
        response = client.post("/query", json={"question": ""})

        assert response.status_code == 422


class TestDocumentsEndpoint:
    """Tests for document management endpoints."""

    def test_list_documents_returns_list(self):
        """GET /documents returns a list of documents."""
        mock_pipeline = MagicMock()
        mock_doc = Document(
            document_id="abc123",
            filename="test.pdf",
            file_type="pdf",
            chunk_count=5,
            content_hash="hash123",
        )
        mock_pipeline.list_documents.return_value = [mock_doc]

        client = _create_test_client(mock_pipeline=mock_pipeline)
        response = client.get("/documents/")

        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 1
        assert len(data["documents"]) == 1
        assert data["documents"][0]["filename"] == "test.pdf"

    def test_delete_document_returns_200(self):
        """DELETE /documents/{id} with mocked pipeline returns 200."""
        mock_pipeline = MagicMock()
        mock_pipeline.delete.return_value = True

        client = _create_test_client(mock_pipeline=mock_pipeline)
        response = client.delete("/documents/abc123")

        assert response.status_code == 200
        assert response.json()["deleted"] == "abc123"

    def test_delete_nonexistent_returns_404(self):
        """DELETE /documents/{id} for non-existent document returns 404."""
        mock_pipeline = MagicMock()
        mock_pipeline.delete.return_value = False

        client = _create_test_client(mock_pipeline=mock_pipeline)
        response = client.delete("/documents/nonexistent")

        assert response.status_code == 404

    def test_upload_unsupported_type_returns_400(self):
        """POST /documents/upload with .exe file returns 400."""
        mock_pipeline = MagicMock()
        client = _create_test_client(mock_pipeline=mock_pipeline)

        response = client.post(
            "/documents/upload",
            files={"file": ("malware.exe", BytesIO(b"bad content"), "application/octet-stream")},
        )

        assert response.status_code == 400
        assert "Unsupported file type" in response.json()["detail"]

    def test_upload_valid_file_returns_metadata(self):
        """POST /documents/upload with valid .txt file returns document metadata."""
        mock_pipeline = MagicMock()
        mock_doc = Document(
            document_id="doc123",
            filename="test.txt",
            file_type="txt",
            chunk_count=3,
            content_hash="hash456",
        )
        mock_pipeline.ingest.return_value = mock_doc

        client = _create_test_client(mock_pipeline=mock_pipeline)
        response = client.post(
            "/documents/upload",
            files={"file": ("test.txt", BytesIO(b"Some test content"), "text/plain")},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["document_id"] == "doc123"
        assert data["chunk_count"] == 3
