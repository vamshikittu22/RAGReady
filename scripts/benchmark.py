"""Benchmark: Naive (dense-only) vs Hybrid retrieval comparison.

Runs the golden dataset through both DenseRetriever and HybridRetriever,
computes context recall and precision for each, and generates a comparison report.

Usage: python scripts/benchmark.py [--output reports/]

This module is both a standalone CLI script and an importable module.
test_benchmark.py imports run_benchmark() and print_benchmark_table()
to avoid logic duplication.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Add src/ to path for standalone execution
_src_path = str(Path(__file__).resolve().parent.parent / "src")
if _src_path not in sys.path:
    sys.path.insert(0, _src_path)

# Add project root to path for tests.evaluation.metrics imports
_project_root = str(Path(__file__).resolve().parent.parent)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from sentence_transformers import SentenceTransformer

from ragready.core.models import ScoredChunk
from ragready.ingestion.pipeline import IngestionPipeline
from ragready.retrieval.dense import DenseRetriever
from ragready.retrieval.hybrid import HybridRetriever, create_retriever

from tests.evaluation.metrics.context_precision import compute_context_precision
from tests.evaluation.metrics.context_recall import compute_context_recall


def run_benchmark(
    pipeline: IngestionPipeline,
    golden_dataset: dict,
    embedding_model: SentenceTransformer,
) -> dict[str, Any]:
    """Run naive vs hybrid benchmark comparison.

    Creates both DenseRetriever and HybridRetriever from the pipeline,
    runs all non-refusal golden dataset questions through both, and
    computes Context Recall and Context Precision for each.

    Args:
        pipeline: Ingested IngestionPipeline with documents indexed.
        golden_dataset: Parsed golden dataset dict with 'entries' key.
        embedding_model: Pre-loaded SentenceTransformer for metric computation.

    Returns:
        Benchmark results dict with metrics, improvement percentages, and winner.
    """
    # Create both retrievers from the pipeline
    dense_retriever = DenseRetriever(chroma=pipeline.chroma)
    hybrid_retriever = create_retriever(
        chroma=pipeline.chroma,
        bm25=pipeline.bm25,
    )

    # Filter to non-refusal entries
    non_refusal_entries = [
        entry for entry in golden_dataset["entries"]
        if not entry.get("should_refuse", False)
    ]

    # Run retrieval for both strategies
    naive_results: list[tuple[dict, list[ScoredChunk]]] = []
    hybrid_results: list[tuple[dict, list[ScoredChunk]]] = []

    for entry in non_refusal_entries:
        question = entry["question"]
        naive_chunks = dense_retriever.retrieve(question)
        hybrid_chunks = hybrid_retriever.retrieve(question)
        naive_results.append((entry, naive_chunks))
        hybrid_results.append((entry, hybrid_chunks))

    # Prepare data for metric computation
    naive_entries = [entry for entry, _ in naive_results]
    naive_chunks = [chunks for _, chunks in naive_results]
    naive_questions = [entry["question"] for entry in naive_entries]

    hybrid_entries = [entry for entry, _ in hybrid_results]
    hybrid_chunks = [chunks for _, chunks in hybrid_results]
    hybrid_questions = [entry["question"] for entry in hybrid_entries]

    # Compute metrics for naive (dense-only)
    naive_context_recall = compute_context_recall(
        golden_entries=naive_entries,
        retrieved_contexts=naive_chunks,
        model=embedding_model,
    )
    naive_context_precision = compute_context_precision(
        questions=naive_questions,
        retrieved_contexts=naive_chunks,
        model=embedding_model,
    )

    # Compute metrics for hybrid
    hybrid_context_recall = compute_context_recall(
        golden_entries=hybrid_entries,
        retrieved_contexts=hybrid_chunks,
        model=embedding_model,
    )
    hybrid_context_precision = compute_context_precision(
        questions=hybrid_questions,
        retrieved_contexts=hybrid_chunks,
        model=embedding_model,
    )

    # Compute improvement percentages
    def _pct_change(baseline: float, improved: float) -> str:
        if baseline == 0:
            return "+inf%" if improved > 0 else "0%"
        change = ((improved - baseline) / baseline) * 100
        sign = "+" if change >= 0 else ""
        return f"{sign}{change:.0f}%"

    recall_improvement = _pct_change(naive_context_recall, hybrid_context_recall)
    precision_improvement = _pct_change(naive_context_precision, hybrid_context_precision)

    # Determine winner
    hybrid_total = hybrid_context_recall + hybrid_context_precision
    naive_total = naive_context_recall + naive_context_precision
    winner = "hybrid" if hybrid_total >= naive_total else "naive"

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "metrics": {
            "naive": {
                "context_recall": round(naive_context_recall, 4),
                "context_precision": round(naive_context_precision, 4),
            },
            "hybrid": {
                "context_recall": round(hybrid_context_recall, 4),
                "context_precision": round(hybrid_context_precision, 4),
            },
        },
        "improvement": {
            "context_recall": recall_improvement,
            "context_precision": precision_improvement,
        },
        "winner": winner,
        "dataset_size": len(non_refusal_entries),
    }


def print_benchmark_table(results: dict[str, Any]) -> None:
    """Print a formatted benchmark comparison table to stdout.

    Args:
        results: Results dict from run_benchmark().
    """
    naive = results["metrics"]["naive"]
    hybrid = results["metrics"]["hybrid"]
    improvement = results["improvement"]

    print()
    print("+---------------------+--------+--------+-------------+")
    print("| Metric              | Naive  | Hybrid | Improvement |")
    print("+---------------------+--------+--------+-------------+")
    print(
        f"| Context Recall      | {naive['context_recall']:.4f} | "
        f"{hybrid['context_recall']:.4f} | {improvement['context_recall']:>11s} |"
    )
    print(
        f"| Context Precision   | {naive['context_precision']:.4f} | "
        f"{hybrid['context_precision']:.4f} | {improvement['context_precision']:>11s} |"
    )
    print("+---------------------+--------+--------+-------------+")
    print(f"\nWinner: {results['winner'].upper()}")
    print(f"Dataset: {results['dataset_size']} non-refusal questions")
    print()


def _load_golden_dataset() -> dict:
    """Load golden dataset from the standard location."""
    dataset_path = Path(__file__).resolve().parent.parent / "tests" / "evaluation" / "golden_dataset.json"
    with open(dataset_path, encoding="utf-8") as f:
        return json.load(f)


def _create_temp_pipeline(tmp_dir: str) -> IngestionPipeline:
    """Create a temporary IngestionPipeline and ingest fixture documents."""
    from ragready.core.config import Settings
    from ragready.ingestion.chunker import DocumentChunker
    from ragready.ingestion.extractors import create_default_registry
    from ragready.storage.bm25_store import BM25Store
    from ragready.storage.chroma import ChromaStore
    from ragready.storage.document_store import DocumentStore

    settings = Settings(
        chroma_persist_dir=str(Path(tmp_dir) / "chroma"),
        bm25_persist_path=str(Path(tmp_dir) / "bm25_index.pkl"),
    )

    registry = create_default_registry()
    chunker = DocumentChunker(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
    )
    chroma = ChromaStore(settings=settings)
    bm25 = BM25Store(settings=settings)
    doc_store = DocumentStore(
        manifest_path=Path(tmp_dir) / "documents.json",
    )

    pipeline = IngestionPipeline(
        extractor_registry=registry,
        chunker=chunker,
        chroma=chroma,
        bm25=bm25,
        doc_store=doc_store,
    )

    # Ingest fixture documents
    fixtures_dir = Path(__file__).resolve().parent.parent / "tests" / "evaluation" / "fixtures"
    for doc_path in sorted(fixtures_dir.glob("*.md")):
        pipeline.ingest(doc_path)

    return pipeline


def main() -> None:
    """CLI entry point for benchmark comparison."""
    parser = argparse.ArgumentParser(
        description="Benchmark: Naive (dense-only) vs Hybrid retrieval comparison.",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="reports",
        help="Output directory for JSON report (default: reports/)",
    )
    args = parser.parse_args()

    print("Loading golden dataset...")
    golden_dataset = _load_golden_dataset()

    print("Loading embedding model...")
    model = SentenceTransformer("all-MiniLM-L6-v2")

    tmp_dir = tempfile.mkdtemp(prefix="ragready-benchmark-")
    try:
        print("Creating pipeline and ingesting fixture documents...")
        pipeline = _create_temp_pipeline(tmp_dir)

        print("Running benchmark...")
        results = run_benchmark(pipeline, golden_dataset, model)

        print_benchmark_table(results)

        # Save report
        output_dir = Path(args.output)
        output_dir.mkdir(exist_ok=True)
        report_path = output_dir / f"benchmark-{datetime.now(timezone.utc).strftime('%Y%m%d')}.json"
        report_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
        print(f"Report saved to: {report_path}")
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


if __name__ == "__main__":
    main()
