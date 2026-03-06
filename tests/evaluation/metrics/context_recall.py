"""Context recall metric for RAG evaluation.

Measures how well the retrieval system recalls the expected context for each
question. High context recall means the retriever finds most of the relevant
information needed to answer correctly.

**Approach:**
- For each golden entry with expected_contexts, embed all expected context
  snippets and all actually retrieved chunk texts using a SentenceTransformer.
- An expected context is considered "recalled" if any retrieved chunk has
  cosine similarity > 0.7 with it.
- Context Recall = (recalled expected contexts) / (total expected contexts).

**Limitations:**
- Relies on embedding similarity, not exact match — semantically different
  but topically related chunks may match.
- Threshold of 0.7 is a heuristic; optimal value depends on domain.
- Does not account for partial recall (a chunk containing half the expected
  information scores the same as a perfect match if above threshold).

**Empty input handling:** Returns 1.0 if no entries with expected contexts
exist (nothing to recall).
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


def compute_context_recall(
    golden_entries: list[dict],
    retrieved_contexts: list[list[ScoredChunk]],
    model: SentenceTransformer,
    threshold: float = 0.7,
) -> float:
    """Compute context recall using embedding cosine similarity.

    For each golden entry with expected_contexts, checks whether the retrieved
    chunks contain semantically similar content. An expected context is
    "recalled" if any retrieved chunk has cosine similarity above the threshold.

    Args:
        golden_entries: List of golden dataset entries. Each entry is a dict
            with optional 'expected_contexts' (list[str]) and 'should_refuse'
            (bool) fields.
        retrieved_contexts: List of retrieved chunks for each entry.
        model: Pre-loaded SentenceTransformer model for embedding.
        threshold: Cosine similarity threshold for recall (default 0.7).

    Returns:
        Fraction of expected contexts that were recalled (0.0-1.0).
        Returns 1.0 if no entries have expected contexts to check.
    """
    if not golden_entries:
        return 1.0

    total_expected = 0
    total_recalled = 0

    for entry, chunks in zip(golden_entries, retrieved_contexts):
        # Skip refusal entries (no expected contexts to check)
        if entry.get("should_refuse", False):
            continue

        expected_contexts = entry.get("expected_contexts", [])
        if not expected_contexts:
            continue

        # Get retrieved chunk texts
        retrieved_texts = [chunk.chunk.text for chunk in chunks]
        if not retrieved_texts:
            # No chunks retrieved — none recalled
            total_expected += len(expected_contexts)
            continue

        # Encode all texts
        expected_embeddings = model.encode(expected_contexts, convert_to_numpy=True)
        retrieved_embeddings = model.encode(retrieved_texts, convert_to_numpy=True)

        for exp_emb in expected_embeddings:
            total_expected += 1
            # Check if any retrieved chunk is similar enough
            for ret_emb in retrieved_embeddings:
                if _cosine_similarity(exp_emb, ret_emb) > threshold:
                    total_recalled += 1
                    break  # Only count once per expected context

    if total_expected == 0:
        return 1.0

    return total_recalled / total_expected
