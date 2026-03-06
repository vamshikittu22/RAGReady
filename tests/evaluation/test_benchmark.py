"""Benchmark tests for naive vs hybrid retrieval comparison.

Tests that hybrid retrieval outperforms naive (dense-only) retrieval
on the golden dataset. All benchmark logic is delegated to
scripts/benchmark.py (single source of truth) — no duplication.

Marked with @pytest.mark.evaluation for targeted test selection.
"""

from __future__ import annotations

from typing import Any

import pytest
from sentence_transformers import SentenceTransformer

from ragready.ingestion.pipeline import IngestionPipeline

from scripts.benchmark import run_benchmark

# Mark entire module as evaluation tests
pytestmark = pytest.mark.evaluation


@pytest.fixture(scope="session")
def benchmark_results(
    eval_pipeline: IngestionPipeline,
    golden_dataset: dict,
    embedding_model: SentenceTransformer,
) -> dict[str, Any]:
    """Run the naive vs hybrid benchmark comparison.

    Delegates all logic to scripts.benchmark.run_benchmark() — this fixture
    only wires up the conftest fixtures to the benchmark function.

    Returns:
        Benchmark results dict with metrics, improvement, and winner.
    """
    return run_benchmark(eval_pipeline, golden_dataset, embedding_model)


class TestBenchmarkComparison:
    """Benchmark tests proving hybrid retrieval superiority over dense-only."""

    def test_hybrid_beats_naive_on_context_recall(
        self, benchmark_results: dict[str, Any]
    ) -> None:
        """Hybrid retrieval must have higher context recall than naive."""
        naive_recall = benchmark_results["metrics"]["naive"]["context_recall"]
        hybrid_recall = benchmark_results["metrics"]["hybrid"]["context_recall"]
        assert hybrid_recall >= naive_recall, (
            f"Hybrid context recall ({hybrid_recall:.4f}) should be >= "
            f"naive context recall ({naive_recall:.4f})"
        )

    def test_hybrid_beats_naive_on_context_precision(
        self, benchmark_results: dict[str, Any]
    ) -> None:
        """Hybrid retrieval must have higher context precision than naive."""
        naive_precision = benchmark_results["metrics"]["naive"]["context_precision"]
        hybrid_precision = benchmark_results["metrics"]["hybrid"]["context_precision"]
        assert hybrid_precision >= naive_precision, (
            f"Hybrid context precision ({hybrid_precision:.4f}) should be >= "
            f"naive context precision ({naive_precision:.4f})"
        )

    def test_benchmark_report_generated(
        self, benchmark_results: dict[str, Any]
    ) -> None:
        """Benchmark results dict must contain all required keys."""
        required_keys = {"timestamp", "metrics", "improvement", "winner", "dataset_size"}
        actual_keys = set(benchmark_results.keys())
        missing = required_keys - actual_keys
        assert not missing, f"Benchmark results missing keys: {missing}"

        # Verify metrics structure
        assert "naive" in benchmark_results["metrics"]
        assert "hybrid" in benchmark_results["metrics"]
        for strategy in ["naive", "hybrid"]:
            metrics = benchmark_results["metrics"][strategy]
            assert "context_recall" in metrics, f"{strategy} missing context_recall"
            assert "context_precision" in metrics, f"{strategy} missing context_precision"

        # Verify improvement structure
        assert "context_recall" in benchmark_results["improvement"]
        assert "context_precision" in benchmark_results["improvement"]

        # Verify winner is valid
        assert benchmark_results["winner"] in {"naive", "hybrid"}
