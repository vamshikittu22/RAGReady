"""Integration tests for the full retrieval pipeline: ingest → retrieve.

Tests the end-to-end flow from document ingestion through hybrid retrieval
(dense + sparse + RRF fusion), document management (list, delete), and
configurable top-k.
"""

import os
import textwrap

import pytest

from ragready.core.config import Settings
from ragready.ingestion.pipeline import IngestionPipeline, create_pipeline
from ragready.retrieval import HybridRetriever, create_retriever


@pytest.fixture()
def pipeline(tmp_path):
    """Create an IngestionPipeline using temporary storage paths."""
    settings = Settings(
        chroma_persist_dir=str(tmp_path / "chroma"),
        bm25_persist_path=str(tmp_path / "bm25_index.pkl"),
    )
    # Need a custom pipeline with a custom DocumentStore path too
    from ragready.ingestion.chunker import DocumentChunker
    from ragready.ingestion.extractors import create_default_registry
    from ragready.storage.bm25_store import BM25Store
    from ragready.storage.chroma import ChromaStore
    from ragready.storage.document_store import DocumentStore

    registry = create_default_registry()
    chunker = DocumentChunker(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
    )
    chroma = ChromaStore(settings=settings)
    bm25 = BM25Store(settings=settings)
    doc_store = DocumentStore(manifest_path=tmp_path / "documents.json")
    return IngestionPipeline(
        extractor_registry=registry,
        chunker=chunker,
        chroma=chroma,
        bm25=bm25,
        doc_store=doc_store,
    )


@pytest.fixture()
def sample_text():
    """Known content about Python for testing retrieval relevance."""
    return textwrap.dedent("""\
        Python is a high-level, general-purpose programming language created by
        Guido van Rossum. Its design philosophy emphasizes code readability with
        the use of significant indentation. Python supports multiple programming
        paradigms, including structured, object-oriented, and functional programming.

        Python was conceived in the late 1980s by Guido van Rossum at Centrum
        Wiskunde & Informatica (CWI) in the Netherlands. Its implementation began
        in December 1989. Van Rossum shouldered sole responsibility for the project
        until July 2018, when he announced his permanent vacation from his role as
        Python's chief architect.

        Python consistently ranks as one of the most popular programming languages.
        It is used in web development, data science, artificial intelligence,
        scientific computing, and many other fields. Popular frameworks include
        Django and Flask for web development, NumPy and pandas for data analysis,
        and TensorFlow and PyTorch for machine learning.

        The Python Package Index (PyPI) hosts over 400,000 packages that extend
        Python's functionality. The pip tool is used to install packages from PyPI.
        Virtual environments isolate project dependencies to avoid conflicts
        between different projects.
    """)


@pytest.fixture()
def sample_file(tmp_path, sample_text):
    """Create a text file with sample content."""
    path = tmp_path / "python_overview.txt"
    path.write_text(sample_text, encoding="utf-8")
    return path


@pytest.fixture()
def ingested_pipeline(pipeline, sample_file):
    """Pipeline with one document already ingested."""
    pipeline.ingest(sample_file)
    return pipeline


@pytest.fixture()
def retriever(ingested_pipeline):
    """HybridRetriever wired to the ingested pipeline's stores."""
    return create_retriever(
        chroma=ingested_pipeline.chroma,
        bm25=ingested_pipeline.bm25,
    )


class TestHybridRetrieval:
    """Tests for hybrid retrieval (dense + sparse + RRF fusion)."""

    def test_semantic_query_returns_relevant_results(self, retriever):
        """Query with a semantic question returns relevant chunks."""
        results = retriever.retrieve("Who created Python?")

        assert len(results) > 0
        assert len(results) <= 5  # default final_top_k

        # At least one result should mention Guido or Python
        texts = " ".join(r.chunk.text for r in results)
        assert "Guido" in texts or "Python" in texts

    def test_keyword_query_finds_exact_match(self, retriever):
        """Query with an exact phrase returns BM25-matched results."""
        results = retriever.retrieve("Centrum Wiskunde Informatica Netherlands")

        assert len(results) > 0
        # BM25 should find chunks with these exact keywords
        texts = " ".join(r.chunk.text for r in results)
        assert "Centrum" in texts or "Netherlands" in texts

    def test_result_structure(self, retriever):
        """Each ScoredChunk has valid fields after fusion."""
        results = retriever.retrieve("programming language")

        assert len(results) > 0
        for r in results:
            assert r.chunk.chunk_id  # non-empty
            assert r.chunk.text  # non-empty
            assert r.score > 0
            assert r.source == "fused"

    def test_empty_query_does_not_crash(self, retriever):
        """Empty or very short query handles gracefully."""
        # Should not raise any exception
        results = retriever.retrieve("")
        assert isinstance(results, list)

        results_short = retriever.retrieve("a")
        assert isinstance(results_short, list)

    def test_configurable_top_k(self, ingested_pipeline):
        """Custom top_k limits the number of returned results."""
        settings = Settings(final_top_k=2)
        retriever = create_retriever(
            chroma=ingested_pipeline.chroma,
            bm25=ingested_pipeline.bm25,
            settings=settings,
        )
        results = retriever.retrieve("Python programming")
        assert len(results) <= 2


class TestDocumentDeletion:
    """Tests for document deletion and its effect on retrieval."""

    def test_delete_removes_from_retrieval(self, ingested_pipeline):
        """Delete document → retrieval returns empty for that document's content."""
        retriever = create_retriever(
            chroma=ingested_pipeline.chroma,
            bm25=ingested_pipeline.bm25,
        )

        # Before deletion: results should be found
        results_before = retriever.retrieve("Guido van Rossum Python")
        assert len(results_before) > 0

        # Delete the document
        docs = ingested_pipeline.list_documents()
        assert len(docs) == 1
        doc_id = docs[0].document_id
        deleted = ingested_pipeline.delete(doc_id)
        assert deleted is True

        # After deletion: no results (both indexes cleared)
        results_after = retriever.retrieve("Guido van Rossum Python")
        assert len(results_after) == 0


class TestDocumentListing:
    """Tests for document listing functionality."""

    def test_list_documents_after_ingestion(self, tmp_path, pipeline):
        """Ingest 2 files → list_documents returns both with correct metadata."""
        # Create two different files
        file1 = tmp_path / "file1.txt"
        file1.write_text(
            "Machine learning is a subset of artificial intelligence. "
            "It focuses on building systems that learn from data. " * 10,
            encoding="utf-8",
        )
        file2 = tmp_path / "file2.txt"
        file2.write_text(
            "Natural language processing enables computers to understand human language. "
            "Techniques include tokenization, parsing, and sentiment analysis. " * 10,
            encoding="utf-8",
        )

        pipeline.ingest(file1)
        pipeline.ingest(file2)

        docs = pipeline.list_documents()
        assert len(docs) == 2

        filenames = {d.filename for d in docs}
        assert filenames == {"file1.txt", "file2.txt"}

        for doc in docs:
            assert doc.document_id  # non-empty
            assert doc.chunk_count > 0
            assert doc.content_hash  # non-empty
            assert doc.file_type == "plaintext"
