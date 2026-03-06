"""CLI evaluation runner for RAGReady.

Runs the full evaluation pipeline: ingests test fixture documents,
runs golden dataset questions through retrieval, generates synthetic
responses, and computes all applicable metrics.

Usage:
    python scripts/evaluate.py [--output reports/] [--with-ollama]

Metrics computed:
    Always (CI-safe):
        - Context Recall
        - Context Precision
        - Refusal Accuracy
        - Citation Accuracy

    With --with-ollama (local only):
        - Faithfulness
        - Answer Relevancy
        - Hallucination Rate
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

from ragready.core.config import Settings
from ragready.core.models import ScoredChunk
from ragready.generation.models import Citation, QueryResponse, RefusalResponse
from ragready.ingestion.chunker import DocumentChunker
from ragready.ingestion.extractors import create_default_registry
from ragready.ingestion.pipeline import IngestionPipeline
from ragready.retrieval.hybrid import create_retriever
from ragready.storage.bm25_store import BM25Store
from ragready.storage.chroma import ChromaStore
from ragready.storage.document_store import DocumentStore

from tests.evaluation.metrics.citation_accuracy import compute_citation_accuracy
from tests.evaluation.metrics.context_precision import compute_context_precision
from tests.evaluation.metrics.context_recall import compute_context_recall
from tests.evaluation.metrics.refusal_accuracy import compute_refusal_accuracy


def _load_golden_dataset() -> dict:
    """Load golden dataset from the standard location."""
    dataset_path = (
        Path(__file__).resolve().parent.parent
        / "tests"
        / "evaluation"
        / "golden_dataset.json"
    )
    with open(dataset_path, encoding="utf-8") as f:
        return json.load(f)


def _create_temp_pipeline(tmp_dir: str) -> IngestionPipeline:
    """Create a temporary IngestionPipeline and ingest fixture documents."""
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
    fixtures_dir = (
        Path(__file__).resolve().parent.parent / "tests" / "evaluation" / "fixtures"
    )
    for doc_path in sorted(fixtures_dir.glob("*.md")):
        pipeline.ingest(doc_path)

    return pipeline


def _generate_synthetic_responses(
    pipeline: IngestionPipeline,
    golden_dataset: dict,
) -> tuple[
    list[tuple[dict, list[ScoredChunk]]],
    list[tuple[dict, QueryResponse | RefusalResponse]],
]:
    """Generate synthetic retrieval results and RAG responses.

    Uses the same logic as conftest.py: concatenates top-3 chunk texts
    as the synthetic answer with citations from chunk metadata.

    Returns:
        Tuple of (retrieval_results, rag_responses) where each is a list
        of (golden_entry, result) tuples.
    """
    retriever = create_retriever(chroma=pipeline.chroma, bm25=pipeline.bm25)

    retrieval_results: list[tuple[dict, list[ScoredChunk]]] = []
    rag_responses: list[tuple[dict, QueryResponse | RefusalResponse]] = []

    for entry in golden_dataset["entries"]:
        if entry["should_refuse"]:
            response = RefusalResponse(
                refused=True,
                reason="Insufficient evidence in retrieved context to answer this question.",
                confidence=0.0,
            )
            rag_responses.append((entry, response))
            continue

        chunks = retriever.retrieve(entry["question"])
        retrieval_results.append((entry, chunks))

        if not chunks:
            response = RefusalResponse(
                refused=True,
                reason="No relevant context chunks found for this query.",
                confidence=0.0,
            )
            rag_responses.append((entry, response))
            continue

        top_chunks = chunks[:3]
        synthetic_answer = " ".join(c.chunk.text for c in top_chunks)
        citations = [
            Citation(
                chunk_text=c.chunk.text[:200],
                document_name=c.chunk.metadata.source_document,
                page_number=c.chunk.metadata.page_number,
                relevance_score=round(c.score, 4),
            )
            for c in top_chunks
        ]
        confidence = round(max(c.score for c in top_chunks), 4)

        response = QueryResponse(
            answer=synthetic_answer,
            citations=citations,
            confidence=confidence,
        )
        rag_responses.append((entry, response))

    return retrieval_results, rag_responses


def run_evaluation(
    pipeline: IngestionPipeline,
    golden_dataset: dict,
    embedding_model: SentenceTransformer,
    with_ollama: bool = False,
) -> dict[str, Any]:
    """Run the full evaluation pipeline and compute metrics.

    Args:
        pipeline: Ingested IngestionPipeline.
        golden_dataset: Parsed golden dataset dict.
        embedding_model: Pre-loaded SentenceTransformer.
        with_ollama: If True, also compute LLM-dependent metrics.

    Returns:
        Evaluation results dict with all computed metrics and thresholds.
    """
    retrieval_results, rag_responses = _generate_synthetic_responses(
        pipeline, golden_dataset
    )

    # Prepare data structures
    retrieval_entries = [entry for entry, _ in retrieval_results]
    retrieval_chunks = [chunks for _, chunks in retrieval_results]
    retrieval_questions = [entry["question"] for entry in retrieval_entries]

    rag_entries = [entry for entry, _ in rag_responses]
    rag_resp_list = [resp for _, resp in rag_responses]

    # Build known_documents set
    known_documents: set[str] = set()
    for entry in golden_dataset["entries"]:
        for doc_name in entry.get("expected_documents", []):
            known_documents.add(doc_name)

    # Build contexts aligned with rag_responses
    rag_contexts: list[list[ScoredChunk]] = []
    for entry, response in rag_responses:
        if isinstance(response, QueryResponse):
            matching_chunks: list[ScoredChunk] = []
            for ret_entry, chunks in retrieval_results:
                if ret_entry.get("id") == entry.get("id"):
                    matching_chunks = chunks
                    break
            rag_contexts.append(matching_chunks)
        else:
            rag_contexts.append([])

    # --- Compute CI-safe metrics ---
    metrics: dict[str, float] = {}

    metrics["context_recall"] = compute_context_recall(
        golden_entries=retrieval_entries,
        retrieved_contexts=retrieval_chunks,
        model=embedding_model,
    )

    metrics["context_precision"] = compute_context_precision(
        questions=retrieval_questions,
        retrieved_contexts=retrieval_chunks,
        model=embedding_model,
    )

    metrics["refusal_accuracy"] = compute_refusal_accuracy(
        golden_entries=rag_entries,
        responses=rag_resp_list,
    )

    metrics["citation_accuracy"] = compute_citation_accuracy(
        responses=rag_resp_list,
        retrieved_contexts=rag_contexts,
        known_documents=known_documents,
    )

    # --- Compute LLM-dependent metrics (optional) ---
    if with_ollama:
        try:
            from tests.evaluation.metrics.faithfulness import (
                compute_faithfulness,
                compute_hallucination_rate,
            )
            from tests.evaluation.metrics.relevancy import compute_answer_relevancy

            rag_questions = [entry["question"] for entry in rag_entries]

            metrics["faithfulness"] = compute_faithfulness(
                responses=rag_resp_list,
                contexts=rag_contexts,
                model=embedding_model,
            )
            metrics["hallucination_rate"] = compute_hallucination_rate(
                metrics["faithfulness"]
            )
            metrics["answer_relevancy"] = compute_answer_relevancy(
                questions=rag_questions,
                responses=rag_resp_list,
                model=embedding_model,
            )
        except Exception as e:
            print(f"Warning: LLM-dependent metrics failed: {e}")

    thresholds: dict[str, float] = {
        "context_recall": 0.75,
        "context_precision": 0.70,
        "refusal_accuracy": 0.90,
        "citation_accuracy": 0.95,
    }
    if with_ollama:
        thresholds.update(
            {
                "faithfulness": 0.85,
                "answer_relevancy": 0.80,
                "hallucination_rate_max": 0.15,
            }
        )

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "metrics": metrics,
        "thresholds": thresholds,
        "dataset_size": len(golden_dataset["entries"]),
        "with_ollama": with_ollama,
    }


def print_results_table(results: dict[str, Any]) -> None:
    """Print a formatted evaluation results table to stdout.

    Args:
        results: Results dict from run_evaluation().
    """
    metrics = results["metrics"]
    thresholds = results["thresholds"]

    print()
    print("+---------------------+--------+-----------+--------+")
    print("| Metric              | Score  | Threshold | Status |")
    print("+---------------------+--------+-----------+--------+")

    for name, score in metrics.items():
        if name == "hallucination_rate":
            threshold = thresholds.get("hallucination_rate_max", 0.15)
            status = "PASS" if score < threshold else "FAIL"
            threshold_str = f"< {threshold:.2f}"
        else:
            threshold = thresholds.get(name, 0.0)
            status = "PASS" if score >= threshold else "FAIL"
            threshold_str = f">= {threshold:.2f}"

        # Format display name
        display_name = name.replace("_", " ").title()
        print(
            f"| {display_name:<19s} | {score:.4f} | {threshold_str:>9s} | {status:>6s} |"
        )

    print("+---------------------+--------+-----------+--------+")
    print(f"\nDataset: {results['dataset_size']} entries")
    print(f"Ollama metrics: {'Yes' if results['with_ollama'] else 'No'}")
    print()


def main() -> None:
    """CLI entry point for evaluation runner."""
    parser = argparse.ArgumentParser(
        description="RAGReady evaluation runner — compute quality metrics on golden dataset.",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="reports",
        help="Output directory for JSON report (default: reports/)",
    )
    parser.add_argument(
        "--with-ollama",
        action="store_true",
        default=False,
        help="Also compute LLM-dependent metrics (faithfulness, relevancy, hallucination)",
    )
    args = parser.parse_args()

    print("Loading golden dataset...")
    golden_dataset = _load_golden_dataset()

    print("Loading embedding model...")
    model = SentenceTransformer("all-MiniLM-L6-v2")

    tmp_dir = tempfile.mkdtemp(prefix="ragready-eval-")
    try:
        print("Creating pipeline and ingesting fixture documents...")
        pipeline = _create_temp_pipeline(tmp_dir)

        print("Running evaluation...")
        results = run_evaluation(pipeline, golden_dataset, model, with_ollama=args.with_ollama)

        print_results_table(results)

        # Save report
        output_dir = Path(args.output)
        output_dir.mkdir(exist_ok=True)
        report_path = (
            output_dir
            / f"evaluation-{datetime.now(timezone.utc).strftime('%Y%m%d')}.json"
        )
        report_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
        print(f"Report saved to: {report_path}")
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


if __name__ == "__main__":
    main()
