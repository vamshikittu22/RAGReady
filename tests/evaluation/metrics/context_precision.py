"""Context precision metric for RAG evaluation.

Measures what fraction of retrieved chunks are actually relevant to the
question. High context precision means the retriever avoids returning
irrelevant noise alongside the relevant information.

**Approach:**
- For each question, embed the question and each retrieved chunk using a
  SentenceTransformer model.
- A chunk is considered "relevant" if its cosine similarity with the
  question exceeds 0.3 (intentionally low threshold — measures general
  topical relevance, not exact match).
- Context Precision = (relevant chunks) / (total retrieved chunks).

**Limitations:**
- Low threshold (0.3) means most topically related chunks pass.
- Does not distinguish between marginally and highly relevant chunks.
- Embedding similarity may not capture keyword-specific relevance.

**Empty input handling:** Returns 1.0 if no chunks were retrieved
(nothing wrong if nothing retrieved).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from sentence_transformers import SentenceTransformer

from src.ragready.core.models import ScoredChunk


def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Compute cosine similarity between two vectors."""
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))


def compute_context_precision(
    questions: list[str],
    retrieved_contexts: list[list[ScoredChunk]],
    model: SentenceTransformer,
    threshold: float = 0.3,
) -> float:
    """Compute context precision using embedding cosine similarity.

    For each question, checks how many of the retrieved chunks are semantically
    relevant to the question. Uses a low threshold (0.3) to measure general
    topical relevance.

    Args:
        questions: List of questions.
        retrieved_contexts: List of retrieved chunks for each question.
        model: Pre-loaded SentenceTransformer model for embedding.
        threshold: Cosine similarity threshold for relevance (default 0.3).

    Returns:
        Fraction of retrieved chunks that are relevant (0.0-1.0).
        Returns 1.0 if no chunks were retrieved across all questions.
    """
    if not questions:
        return 1.0

    total_chunks = 0
    relevant_chunks = 0

    for question, chunks in zip(questions, retrieved_contexts):
        if not chunks:
            continue

        # Encode question and all chunk texts
        chunk_texts = [chunk.chunk.text for chunk in chunks]
        all_texts = [question] + chunk_texts
        embeddings = model.encode(all_texts, convert_to_numpy=True)

        question_emb = embeddings[0]
        chunk_embeddings = embeddings[1:]

        for chunk_emb in chunk_embeddings:
            total_chunks += 1
            if _cosine_similarity(question_emb, chunk_emb) > threshold:
                relevant_chunks += 1

    if total_chunks == 0:
        return 1.0

    return relevant_chunks / total_chunks
