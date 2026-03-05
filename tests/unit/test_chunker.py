"""Unit tests for the document chunker and metadata utilities."""

from pathlib import Path

import pytest

from ragready.core.exceptions import ChunkingError, ExtractionError
from ragready.core.models import Chunk
from ragready.ingestion.chunker import DocumentChunker
from ragready.ingestion.metadata import (
    compute_content_hash,
    compute_document_id,
    detect_file_type,
)


# ---------------------------------------------------------------------------
# Metadata utility tests
# ---------------------------------------------------------------------------

class TestComputeContentHash:
    def test_returns_16_hex_chars(self):
        result = compute_content_hash("hello world")
        assert len(result) == 16
        assert all(c in "0123456789abcdef" for c in result)

    def test_deterministic(self):
        assert compute_content_hash("test") == compute_content_hash("test")

    def test_different_inputs_differ(self):
        assert compute_content_hash("a") != compute_content_hash("b")


class TestComputeDocumentId:
    def test_returns_16_hex_chars(self):
        result = compute_document_id("file.txt", "abc123")
        assert len(result) == 16

    def test_deterministic(self):
        a = compute_document_id("file.txt", "hash1")
        b = compute_document_id("file.txt", "hash1")
        assert a == b

    def test_different_inputs_differ(self):
        a = compute_document_id("file1.txt", "hash1")
        b = compute_document_id("file2.txt", "hash1")
        assert a != b


class TestDetectFileType:
    @pytest.mark.parametrize(
        "filename, expected",
        [
            ("doc.pdf", "pdf"),
            ("doc.md", "markdown"),
            ("doc.markdown", "markdown"),
            ("doc.html", "html"),
            ("doc.htm", "html"),
            ("doc.txt", "plaintext"),
            ("doc.text", "plaintext"),
        ],
    )
    def test_supported_extensions(self, filename, expected):
        assert detect_file_type(Path(filename)) == expected

    def test_case_insensitive(self):
        assert detect_file_type(Path("DOC.PDF")) == "pdf"

    def test_unsupported_raises(self):
        with pytest.raises(ExtractionError, match="Unsupported file extension"):
            detect_file_type(Path("data.xlsx"))


# ---------------------------------------------------------------------------
# DocumentChunker tests
# ---------------------------------------------------------------------------

class TestDocumentChunkerInit:
    def test_invalid_chunk_size_raises(self):
        with pytest.raises(ChunkingError, match="chunk_size must be positive"):
            DocumentChunker(chunk_size=0)

    def test_negative_overlap_raises(self):
        with pytest.raises(ChunkingError, match="chunk_overlap must be non-negative"):
            DocumentChunker(chunk_overlap=-1)

    def test_overlap_ge_size_raises(self):
        with pytest.raises(ChunkingError, match="chunk_overlap.*must be less than"):
            DocumentChunker(chunk_size=100, chunk_overlap=100)


class TestDocumentChunkerChunk:
    """Tests for DocumentChunker.chunk()."""

    def setup_method(self):
        self.chunker = DocumentChunker(chunk_size=200, chunk_overlap=30)

    def test_long_text_produces_multiple_chunks(self):
        text = "This is a sentence with some content. " * 100  # ~3800 chars
        chunks = self.chunker.chunk(text, "doc1", "test.txt")
        assert len(chunks) > 1
        assert all(isinstance(c, Chunk) for c in chunks)

    def test_chunks_respect_max_size(self):
        # Use a large enough text to guarantee splitting
        text = "Word " * 500  # 2500 chars
        chunker = DocumentChunker(chunk_size=200, chunk_overlap=30)
        chunks = chunker.chunk(text, "doc1", "test.txt")
        for chunk in chunks:
            # Chunks may slightly exceed chunk_size due to separator logic,
            # but should be in the right ballpark.
            assert len(chunk.text) <= 250  # generous margin

    def test_metadata_populated(self):
        text = "Hello world. " * 200
        chunks = self.chunker.chunk(text, "doc1", "test.txt")
        for i, chunk in enumerate(chunks):
            assert chunk.document_id == "doc1"
            assert chunk.metadata.source_document == "test.txt"
            assert chunk.metadata.chunk_index == i
            assert chunk.metadata.content_hash  # non-empty
            assert chunk.metadata.ingested_at is not None

    def test_position_increases(self):
        text = "Some text with content here. " * 200
        chunks = self.chunker.chunk(text, "doc1", "test.txt")
        positions = [c.metadata.position_in_doc for c in chunks]
        # Positions should be non-decreasing (overlap means they may not be strictly increasing)
        assert positions == sorted(positions)
        # First chunk starts at 0
        assert positions[0] == 0

    def test_chunk_id_deterministic(self):
        text = "Deterministic test content. " * 100
        chunks_a = self.chunker.chunk(text, "doc1", "test.txt")
        chunks_b = self.chunker.chunk(text, "doc1", "test.txt")
        assert [c.chunk_id for c in chunks_a] == [c.chunk_id for c in chunks_b]

    def test_short_text_single_chunk(self):
        text = "Short document."
        chunks = self.chunker.chunk(text, "doc1", "test.txt")
        assert len(chunks) == 1
        assert chunks[0].text == "Short document."

    def test_empty_text_returns_empty_list(self):
        chunks = self.chunker.chunk("", "doc1", "test.txt")
        assert chunks == []

    def test_whitespace_only_returns_empty_list(self):
        chunks = self.chunker.chunk("   \n\n  ", "doc1", "test.txt")
        assert chunks == []

    def test_page_number_estimation(self):
        text = "A" * 1000
        chunker = DocumentChunker(chunk_size=200, chunk_overlap=30)
        chunks = chunker.chunk(text, "doc1", "test.pdf", page_count=5)
        # First chunk should be page 1
        assert chunks[0].metadata.page_number == 1
        # Last chunk should be at most page 5
        assert chunks[-1].metadata.page_number is not None
        assert chunks[-1].metadata.page_number <= 5

    def test_content_hash_correct(self):
        text = "Verify hash is correct."
        chunks = self.chunker.chunk(text, "doc1", "test.txt")
        expected_hash = compute_content_hash("Verify hash is correct.")
        assert chunks[0].metadata.content_hash == expected_hash
