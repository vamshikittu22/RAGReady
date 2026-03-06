"""Evaluation test fixtures for RAGReady.

Provides session-scoped fixtures for the evaluation pipeline, retrievers,
golden dataset, retrieval results, and synthetic RAG responses.

All fixtures are deterministic and work offline without Ollama or any LLM.
Synthetic responses are generated from retrieval results to test the
measurement pipeline itself (not the LLM quality).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from sentence_transformers import SentenceTransformer

from ragready.core.config import Settings
from ragready.core.models import ScoredChunk
from ragready.generation.models import Citation, QueryResponse, RefusalResponse
from ragready.ingestion.chunker import DocumentChunker
from ragready.ingestion.extractors import create_default_registry
from ragready.ingestion.pipeline import IngestionPipeline
from ragready.retrieval.dense import DenseRetriever
from ragready.retrieval.hybrid import HybridRetriever, create_retriever
from ragready.storage.bm25_store import BM25Store
from ragready.storage.chroma import ChromaStore
from ragready.storage.document_store import DocumentStore

# Directory containing test fixture documents
FIXTURES_DIR = Path(__file__).parent / "fixtures"
GOLDEN_DATASET_PATH = Path(__file__).parent / "golden_dataset.json"


@pytest.fixture(scope="session")
def eval_settings(tmp_path_factory: pytest.TempPathFactory) -> Settings:
    """Settings with temporary storage directories for evaluation tests."""
    tmp_dir = tmp_path_factory.mktemp("eval")
    return Settings(
        chroma_persist_dir=str(tmp_dir / "chroma"),
        bm25_persist_path=str(tmp_dir / "bm25_index.pkl"),
    )


@pytest.fixture(scope="session")
def eval_pipeline(eval_settings: Settings) -> IngestionPipeline:
    """IngestionPipeline with all 3 test fixture documents ingested.

    Constructs the pipeline manually (same pattern as integration tests)
    and ingests all fixture documents from tests/evaluation/fixtures/.
    """
    registry = create_default_registry()
    chunker = DocumentChunker(
        chunk_size=eval_settings.chunk_size,
        chunk_overlap=eval_settings.chunk_overlap,
    )
    chroma = ChromaStore(settings=eval_settings)
    bm25 = BM25Store(settings=eval_settings)
    doc_store = DocumentStore(
        manifest_path=Path(eval_settings.chroma_persist_dir).parent / "documents.json",
    )
    pipeline = IngestionPipeline(
        extractor_registry=registry,
        chunker=chunker,
        chroma=chroma,
        bm25=bm25,
        doc_store=doc_store,
    )

    # Ingest all fixture documents
    fixture_files = sorted(FIXTURES_DIR.glob("*.md"))
    assert len(fixture_files) == 3, f"Expected 3 fixture docs, found {len(fixture_files)}"
    for doc_path in fixture_files:
        pipeline.ingest(doc_path)

    return pipeline


@pytest.fixture(scope="session")
def eval_hybrid_retriever(eval_pipeline: IngestionPipeline) -> HybridRetriever:
    """HybridRetriever wired to the evaluation pipeline's ingested stores."""
    return create_retriever(
        chroma=eval_pipeline.chroma,
        bm25=eval_pipeline.bm25,
    )


@pytest.fixture(scope="session")
def eval_dense_retriever(eval_pipeline: IngestionPipeline) -> DenseRetriever:
    """DenseRetriever only (naive baseline for comparison)."""
    return DenseRetriever(chroma=eval_pipeline.chroma)


@pytest.fixture(scope="session")
def golden_dataset() -> dict:
    """Load and return the parsed golden dataset JSON."""
    with open(GOLDEN_DATASET_PATH, encoding="utf-8") as f:
        data = json.load(f)
    assert "entries" in data, "Golden dataset must have 'entries' key"
    assert len(data["entries"]) >= 50, f"Golden dataset must have >= 50 entries, found {len(data['entries'])}"
    return data


@pytest.fixture(scope="session")
def eval_retrieval_results(
    eval_hybrid_retriever: HybridRetriever,
    golden_dataset: dict,
) -> list[tuple[dict, list[ScoredChunk]]]:
    """Run each non-refusal golden dataset question through hybrid retrieval.

    Returns list of (golden_entry, list[ScoredChunk]) tuples.
    This does NOT run the full RAG chain — retrieval only.
    """
    results: list[tuple[dict, list[ScoredChunk]]] = []
    for entry in golden_dataset["entries"]:
        if entry["should_refuse"]:
            continue
        chunks = eval_hybrid_retriever.retrieve(entry["question"])
        results.append((entry, chunks))
    return results


@pytest.fixture(scope="session")
def eval_dense_results(
    eval_dense_retriever: DenseRetriever,
    golden_dataset: dict,
) -> list[tuple[dict, list[ScoredChunk]]]:
    """Run each non-refusal golden dataset question through dense retrieval.

    Returns list of (golden_entry, list[ScoredChunk]) tuples for naive
    baseline comparison against hybrid retrieval.
    """
    results: list[tuple[dict, list[ScoredChunk]]] = []
    for entry in golden_dataset["entries"]:
        if entry["should_refuse"]:
            continue
        chunks = eval_dense_retriever.retrieve(entry["question"])
        results.append((entry, chunks))
    return results


@pytest.fixture(scope="session")
def eval_rag_responses(
    eval_hybrid_retriever: HybridRetriever,
    golden_dataset: dict,
) -> list[tuple[dict, QueryResponse | RefusalResponse]]:
    """Generate synthetic QueryResponse/RefusalResponse for each golden entry.

    Creates deterministic, CI-safe responses WITHOUT calling any LLM:
    - For refusal entries or entries with no retrieval results: RefusalResponse
    - For answerable entries: QueryResponse with synthetic answer from top-3
      chunk texts and citations built from ScoredChunk metadata.

    This ensures faithfulness/citation metrics test the measurement pipeline
    itself, not the LLM quality. Real LLM responses are tested separately
    via @pytest.mark.ollama marked tests.
    """
    results: list[tuple[dict, QueryResponse | RefusalResponse]] = []

    for entry in golden_dataset["entries"]:
        if entry["should_refuse"]:
            # Create a refusal response for out-of-domain questions
            response = RefusalResponse(
                refused=True,
                reason="Insufficient evidence in retrieved context to answer this question.",
                confidence=0.0,
            )
            results.append((entry, response))
            continue

        # Retrieve chunks for this question
        chunks = eval_hybrid_retriever.retrieve(entry["question"])

        if not chunks:
            # No chunks found — refuse
            response = RefusalResponse(
                refused=True,
                reason="No relevant context chunks found for this query.",
                confidence=0.0,
            )
            results.append((entry, response))
            continue

        # Build synthetic answer from top-3 chunk texts
        top_chunks = chunks[:3]
        synthetic_answer = " ".join(c.chunk.text for c in top_chunks)

        # Build citations from ScoredChunk metadata
        citations = [
            Citation(
                chunk_text=c.chunk.text[:200],  # Truncate for compactness
                document_name=c.chunk.metadata.source_document,
                page_number=c.chunk.metadata.page_number,
                relevance_score=round(c.score, 4),
            )
            for c in top_chunks
        ]

        # Confidence based on top retrieval score
        confidence = round(max(c.score for c in top_chunks), 4)

        response = QueryResponse(
            answer=synthetic_answer,
            citations=citations,
            confidence=confidence,
        )
        results.append((entry, response))

    return results


@pytest.fixture(scope="session")
def embedding_model() -> SentenceTransformer:
    """Load all-MiniLM-L6-v2 SentenceTransformer once for metric computations."""
    return SentenceTransformer("all-MiniLM-L6-v2")
