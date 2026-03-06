"""Answer relevancy metric for RAG evaluation.

Measures how relevant the generated answer is to the original question using
embedding cosine similarity. A relevant answer directly addresses the question
topic and provides information the user asked for.

**Approach:**
- Embed both the question and the answer using a SentenceTransformer model.
- Compute cosine similarity between the question and answer embeddings.
- Return the mean cosine similarity across all (question, answer) pairs.

**Limitations:**
- Cosine similarity captures semantic overlap, not logical relevance.
- A semantically similar but factually wrong answer will still score high.
- Very short answers may have inflated or deflated similarity scores.
- Use in conjunction with faithfulness to get a complete picture.

**Empty input handling:** Returns 1.0 if no non-refusal responses to check
(nothing wrong if nothing to check).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from sentence_transformers import SentenceTransformer

from src.ragready.generation.models import QueryResponse, RefusalResponse


def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Compute cosine similarity between two vectors.

    Args:
        a: First vector.
        b: Second vector.

    Returns:
        Cosine similarity between a and b (0.0-1.0 for normalized embeddings).
    """
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))


def compute_answer_relevancy(
    questions: list[str],
    responses: list[QueryResponse | RefusalResponse],
    model: SentenceTransformer,
) -> float:
    """Compute answer relevancy score using embedding cosine similarity.

    For each (question, answer) pair, embeds both texts and computes their
    cosine similarity. RefusalResponse entries are skipped since they don't
    have meaningful answers to score.

    Args:
        questions: List of original questions.
        responses: List of query responses (QueryResponse or RefusalResponse).
        model: Pre-loaded SentenceTransformer model for embedding.

    Returns:
        Mean cosine similarity between questions and their answers (0.0-1.0).
        Returns 1.0 if no non-refusal responses exist.
    """
    if not questions or not responses:
        return 1.0

    # Collect (question, answer) pairs, skipping RefusalResponse
    pairs: list[tuple[str, str]] = []
    for question, response in zip(questions, responses):
        if isinstance(response, QueryResponse):
            pairs.append((question, response.answer))

    if not pairs:
        return 1.0

    # Batch encode all questions and answers
    all_questions = [q for q, _ in pairs]
    all_answers = [a for _, a in pairs]

    question_embeddings = model.encode(all_questions, convert_to_numpy=True)
    answer_embeddings = model.encode(all_answers, convert_to_numpy=True)

    # Compute cosine similarity for each pair
    similarities: list[float] = []
    for q_emb, a_emb in zip(question_embeddings, answer_embeddings):
        sim = _cosine_similarity(q_emb, a_emb)
        similarities.append(sim)

    return float(np.mean(similarities))
