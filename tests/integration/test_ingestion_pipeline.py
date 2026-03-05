"""Integration tests for the full ingestion pipeline.

Tests the end-to-end flow: file → extract → chunk → dual-index,
including duplicate detection, deletion, and sync verification.
"""

from pathlib import Path

import pytest

from ragready.core.config import Settings
from ragready.ingestion.chunker import DocumentChunker
from ragready.ingestion.extractors import create_default_registry
from ragready.ingestion.pipeline import IngestionPipeline
from ragready.storage.bm25_store import BM25Store
from ragready.storage.chroma import ChromaStore
from ragready.storage.document_store import DocumentStore


@pytest.fixture()
def test_settings(tmp_path: Path) -> Settings:
    """Create Settings pointing all storage to a temp directory."""
    return Settings(
        chroma_persist_dir=str(tmp_path / "chroma"),
        bm25_persist_path=str(tmp_path / "bm25_index.pkl"),
    )


@pytest.fixture()
def pipeline(test_settings: Settings, tmp_path: Path) -> IngestionPipeline:
    """Create a fully-wired pipeline with temp storage."""
    registry = create_default_registry()
    chunker = DocumentChunker(
        chunk_size=test_settings.chunk_size,
        chunk_overlap=test_settings.chunk_overlap,
    )
    chroma = ChromaStore(settings=test_settings)
    bm25 = BM25Store(settings=test_settings)
    doc_store = DocumentStore(manifest_path=tmp_path / "documents.json")
    return IngestionPipeline(
        extractor_registry=registry,
        chunker=chunker,
        chroma=chroma,
        bm25=bm25,
        doc_store=doc_store,
    )


@pytest.fixture()
def sample_file(tmp_path: Path) -> Path:
    """Create a test text file with ~1000 chars of content."""
    content = (
        "This is a test document for RAGReady ingestion pipeline. "
        "It contains enough content to be split into multiple chunks. "
    ) * 20  # ~1200 chars
    file_path = tmp_path / "sample.txt"
    file_path.write_text(content, encoding="utf-8")
    return file_path


class TestIngestionPipelineFull:
    """End-to-end integration tests for the ingestion pipeline."""

    def test_ingest_creates_document_and_indexes(
        self, pipeline: IngestionPipeline, sample_file: Path, test_settings: Settings
    ):
        """Ingest a file and verify Document + both indexes are populated."""
        doc = pipeline.ingest(sample_file)

        assert doc.filename == "sample.txt"
        assert doc.file_type == "plaintext"
        assert doc.chunk_count > 0
        assert doc.document_id
        assert doc.content_hash

        # Verify both stores have the right chunk count
        assert pipeline._chroma.count() == doc.chunk_count
        assert pipeline._bm25.count() == doc.chunk_count

        # Verify document manifest
        docs = pipeline._doc_store.list_documents()
        assert len(docs) == 1
        assert docs[0].document_id == doc.document_id

    def test_duplicate_ingestion_returns_existing(
        self, pipeline: IngestionPipeline, sample_file: Path
    ):
        """Ingesting the same file twice should return existing, not duplicate."""
        doc1 = pipeline.ingest(sample_file)
        doc2 = pipeline.ingest(sample_file)

        assert doc1.document_id == doc2.document_id
        assert pipeline._chroma.count() == doc1.chunk_count  # no duplication
        assert pipeline._bm25.count() == doc1.chunk_count

    def test_delete_removes_from_all_stores(
        self, pipeline: IngestionPipeline, sample_file: Path
    ):
        """Deleting a document should remove it from all three stores."""
        doc = pipeline.ingest(sample_file)
        assert pipeline._chroma.count() > 0

        result = pipeline.delete(doc.document_id)
        assert result is True

        assert pipeline._chroma.count() == 0
        assert pipeline._bm25.count() == 0
        assert pipeline._doc_store.list_documents() == []

    def test_delete_nonexistent_returns_false(self, pipeline: IngestionPipeline):
        """Deleting a document that doesn't exist should return False."""
        assert pipeline.delete("nonexistent_id") is False

    def test_verify_sync_after_ingest(
        self, pipeline: IngestionPipeline, sample_file: Path
    ):
        """verify_sync should report in_sync=True after successful ingest."""
        pipeline.ingest(sample_file)
        sync = pipeline._doc_store.verify_sync(pipeline._chroma, pipeline._bm25)
        assert sync["in_sync"] is True
        assert sync["manifest_count"] == 1
        assert sync["chroma_count"] == 1
        assert sync["bm25_count"] == 1
        assert len(sync["missing_from_chroma"]) == 0
        assert len(sync["missing_from_bm25"]) == 0

    def test_file_not_found_raises(self, pipeline: IngestionPipeline):
        """Ingesting a nonexistent file should raise FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            pipeline.ingest(Path("/nonexistent/file.txt"))

    def test_multiple_documents(
        self, pipeline: IngestionPipeline, tmp_path: Path
    ):
        """Ingest multiple different files and verify counts."""
        file1 = tmp_path / "doc1.txt"
        file1.write_text("First document content. " * 50, encoding="utf-8")
        file2 = tmp_path / "doc2.txt"
        file2.write_text("Second document with different content. " * 50, encoding="utf-8")

        doc1 = pipeline.ingest(file1)
        doc2 = pipeline.ingest(file2)

        assert doc1.document_id != doc2.document_id
        assert pipeline._chroma.count() == doc1.chunk_count + doc2.chunk_count
        assert pipeline._bm25.count() == doc1.chunk_count + doc2.chunk_count
        assert len(pipeline._doc_store.list_documents()) == 2

        sync = pipeline._doc_store.verify_sync(pipeline._chroma, pipeline._bm25)
        assert sync["in_sync"] is True
