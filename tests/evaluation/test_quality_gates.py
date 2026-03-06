"""Quality gate tests for RAG evaluation metrics.

Tests all 7 metric thresholds to catch quality regressions:

**CI-safe tests (retrieval + deterministic, run on every PR):**
- Context recall >= 0.75
- Context precision >= 0.70
- Refusal accuracy >= 0.90
- Citation accuracy >= 0.95

**Local-only tests (LLM-dependent, marked @pytest.mark.ollama):**
- Faithfulness >= 0.85
- Answer relevancy >= 0.80
- Hallucination rate < 0.15

CI tests use synthetic responses (no LLM needed). Local tests
produce meaningful results only with real LLM-generated responses.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pytest
from sentence_transformers import SentenceTransformer

from ragready.core.models import ScoredChunk
from ragready.generation.models import QueryResponse, RefusalResponse

from tests.evaluation.metrics.citation_accuracy import compute_citation_accuracy
from tests.evaluation.metrics.context_precision import compute_context_precision
from tests.evaluation.metrics.context_recall import compute_context_recall
from tests.evaluation.metrics.faithfulness import (
    compute_faithfulness,
    compute_hallucination_rate,
)
from tests.evaluation.metrics.refusal_accuracy import compute_refusal_accuracy
from tests.evaluation.metrics.relevancy import compute_answer_relevancy

# Mark entire module as evaluation tests
pytestmark = pytest.mark.evaluation


@pytest.fixture(scope="session")
def eval_metrics(
    golden_dataset: dict,
    eval_retrieval_results: list[tuple[dict, list[ScoredChunk]]],
    eval_rag_responses: list[tuple[dict, QueryResponse | RefusalResponse]],
    embedding_model: SentenceTransformer,
) -> dict[str, float]:
    """Compute all applicable metrics once and cache for all quality gate tests.

    CI-safe metrics (retrieval-only + deterministic):
    - context_recall, context_precision: embedding-based retrieval metrics
    - refusal_accuracy, citation_accuracy: deterministic checks

    LLM-dependent metrics (local-only):
    - faithfulness, hallucination_rate: require real LLM responses for meaningful results
    - answer_relevancy: embedding similarity between question and answer

    Returns dict mapping metric name to score (0.0-1.0).
    """
    # Prepare data structures from fixtures
    # Retrieval results: list of (golden_entry, list[ScoredChunk])
    retrieval_entries = [entry for entry, _ in eval_retrieval_results]
    retrieval_chunks = [chunks for _, chunks in eval_retrieval_results]

    # RAG responses: list of (golden_entry, response)
    rag_entries = [entry for entry, _ in eval_rag_responses]
    rag_responses = [resp for _, resp in eval_rag_responses]

    # Build known_documents set from golden dataset expected_documents
    known_documents: set[str] = set()
    for entry in golden_dataset["entries"]:
        for doc_name in entry.get("expected_documents", []):
            known_documents.add(doc_name)

    # Build contexts list aligned with rag_responses for citation/faithfulness
    rag_contexts: list[list[ScoredChunk]] = []
    for entry, response in eval_rag_responses:
        if isinstance(response, QueryResponse):
            # Find matching retrieval results for this entry
            matching_chunks = []
            for ret_entry, chunks in eval_retrieval_results:
                if ret_entry.get("id") == entry.get("id"):
                    matching_chunks = chunks
                    break
            rag_contexts.append(matching_chunks)
        else:
            rag_contexts.append([])

    # Questions list aligned with retrieval results
    retrieval_questions = [entry["question"] for entry in retrieval_entries]

    # Questions list aligned with rag responses
    rag_questions = [entry["question"] for entry in rag_entries]

    # --- Compute CI-safe metrics ---
    context_recall = compute_context_recall(
        golden_entries=retrieval_entries,
        retrieved_contexts=retrieval_chunks,
        model=embedding_model,
    )

    context_precision = compute_context_precision(
        questions=retrieval_questions,
        retrieved_contexts=retrieval_chunks,
        model=embedding_model,
    )

    refusal_accuracy = compute_refusal_accuracy(
        golden_entries=rag_entries,
        responses=rag_responses,
    )

    citation_accuracy = compute_citation_accuracy(
        responses=rag_responses,
        retrieved_contexts=rag_contexts,
        known_documents=known_documents,
    )

    # --- Compute LLM-dependent metrics (with synthetic data for CI) ---
    faithfulness = compute_faithfulness(
        responses=rag_responses,
        contexts=rag_contexts,
        model=embedding_model,
    )

    hallucination_rate = compute_hallucination_rate(faithfulness)

    answer_relevancy = compute_answer_relevancy(
        questions=rag_questions,
        responses=rag_responses,
        model=embedding_model,
    )

    metrics: dict[str, float] = {
        "context_recall": context_recall,
        "context_precision": context_precision,
        "refusal_accuracy": refusal_accuracy,
        "citation_accuracy": citation_accuracy,
        "faithfulness": faithfulness,
        "hallucination_rate": hallucination_rate,
        "answer_relevancy": answer_relevancy,
    }

    # Write report to reports/ directory for artifact collection
    reports_dir = Path("reports")
    reports_dir.mkdir(exist_ok=True)
    report_path = reports_dir / f"evaluation-{datetime.now(timezone.utc).strftime('%Y%m%d')}.json"
    report: dict[str, Any] = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "metrics": metrics,
        "thresholds": {
            "context_recall": 0.75,
            "context_precision": 0.70,
            "refusal_accuracy": 0.90,
            "citation_accuracy": 0.95,
            "faithfulness": 0.85,
            "answer_relevancy": 0.80,
            "hallucination_rate_max": 0.15,
        },
        "dataset_size": len(golden_dataset["entries"]),
    }
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    return metrics


# ============================================================================
# CI-safe tests (retrieval-only + deterministic, run on every PR)
# ============================================================================


class TestCISafeQualityGates:
    """Quality gate tests that run in CI without Ollama or any LLM."""

    def test_context_recall_above_threshold(
        self, eval_metrics: dict[str, float]
    ) -> None:
        """Context recall must be >= 0.75 to ensure retriever finds expected info."""
        score = eval_metrics["context_recall"]
        assert score >= 0.75, f"Context Recall {score:.3f} below threshold 0.75"

    def test_context_precision_above_threshold(
        self, eval_metrics: dict[str, float]
    ) -> None:
        """Context precision must be >= 0.70 to ensure low retrieval noise."""
        score = eval_metrics["context_precision"]
        assert score >= 0.70, f"Context Precision {score:.3f} below threshold 0.70"

    def test_refusal_accuracy_above_threshold(
        self, eval_metrics: dict[str, float]
    ) -> None:
        """Refusal accuracy must be >= 0.90 to ensure correct refuse/answer decisions."""
        score = eval_metrics["refusal_accuracy"]
        assert score >= 0.90, f"Refusal Accuracy {score:.3f} below threshold 0.90"

    def test_citation_accuracy_above_threshold(
        self, eval_metrics: dict[str, float]
    ) -> None:
        """Citation accuracy must be >= 0.95 to ensure citations reference real content."""
        score = eval_metrics["citation_accuracy"]
        assert score >= 0.95, f"Citation Accuracy {score:.3f} below threshold 0.95"


# ============================================================================
# Local-only tests (LLM-dependent, skipped in CI)
# ============================================================================


@pytest.mark.ollama
@pytest.mark.slow
class TestLocalOnlyQualityGates:
    """Quality gate tests requiring real LLM responses.

    These tests only produce meaningful results when run locally with Ollama
    and real LLM-generated responses. In CI (which excludes @pytest.mark.ollama),
    they are automatically skipped.

    With synthetic responses (CI mode), faithfulness and answer relevancy
    scores reflect the measurement pipeline, not actual LLM quality.
    """

    def test_faithfulness_above_threshold(
        self, eval_metrics: dict[str, float]
    ) -> None:
        """Faithfulness must be >= 0.85 to ensure answers are grounded in context."""
        score = eval_metrics["faithfulness"]
        assert score >= 0.85, f"Faithfulness {score:.3f} below threshold 0.85"

    def test_answer_relevancy_above_threshold(
        self, eval_metrics: dict[str, float]
    ) -> None:
        """Answer relevancy must be >= 0.80 to ensure answers address the question."""
        score = eval_metrics["answer_relevancy"]
        assert score >= 0.80, f"Answer Relevancy {score:.3f} below threshold 0.80"

    def test_hallucination_rate_below_threshold(
        self, eval_metrics: dict[str, float]
    ) -> None:
        """Hallucination rate must be < 0.15 (complement of faithfulness >= 0.85)."""
        score = eval_metrics["hallucination_rate"]
        assert score < 0.15, f"Hallucination Rate {score:.3f} above threshold 0.15"
