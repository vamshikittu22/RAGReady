"""Faithfulness metric for RAG evaluation.

Measures how faithfully the generated answer is grounded in the retrieved context.
A faithful answer contains only claims that can be verified from the context chunks.

**Approach (layered fallback):**

1. **HHEM (primary):** Uses the Vectara Hallucination Evaluation Model
   (vectara/hallucination_evaluation_model) via HuggingFace transformers.
   For each (answer, concatenated context) pair, the model classifies whether
   the answer is consistent with the context. Score = mean of consistent labels.

2. **Embedding cosine similarity (fallback):** If HHEM loading fails, falls back
   to sentence-transformers. Each answer sentence is embedded alongside the
   concatenated context, and cosine similarity is computed. Sentences with
   similarity > 0.5 are considered "faithful." Score = fraction of faithful
   sentences.

**Limitations:**
- No LLM judge — relies on classifier or embedding similarity.
- HHEM is a cross-encoder (~100M params), less nuanced than GPT-4 judge.
- Embedding fallback only captures semantic similarity, not logical entailment.
- Does not detect subtle logical contradictions or numerical errors.

**Empty input handling:** Returns 1.0 if no non-refusal responses to check
(nothing wrong if nothing to check).
"""

from __future__ import annotations

import logging
import re
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from sentence_transformers import SentenceTransformer

from src.ragready.core.models import ScoredChunk
from src.ragready.generation.models import QueryResponse, RefusalResponse

logger = logging.getLogger(__name__)

# Module-level cache for HHEM model/tokenizer
_hhem_model = None
_hhem_tokenizer = None
_hhem_available: bool | None = None


def _try_load_hhem() -> bool:
    """Attempt to load the HHEM model. Returns True if successful."""
    global _hhem_model, _hhem_tokenizer, _hhem_available

    if _hhem_available is not None:
        return _hhem_available

    try:
        from transformers import AutoModelForSequenceClassification, AutoTokenizer

        _hhem_tokenizer = AutoTokenizer.from_pretrained(
            "vectara/hallucination_evaluation_model"
        )
        _hhem_model = AutoModelForSequenceClassification.from_pretrained(
            "vectara/hallucination_evaluation_model"
        )
        _hhem_available = True
        logger.info("HHEM model loaded successfully")
    except Exception as e:
        logger.warning("HHEM model unavailable, will use embedding fallback: %s", e)
        _hhem_available = False

    return _hhem_available


def _score_with_hhem(answer: str, context: str) -> float:
    """Score faithfulness using HHEM classifier.

    Args:
        answer: The generated answer text.
        context: Concatenated context text from retrieved chunks.

    Returns:
        Probability that the answer is consistent with the context (0.0-1.0).
    """
    import torch

    assert _hhem_tokenizer is not None
    assert _hhem_model is not None

    inputs = _hhem_tokenizer(
        context,
        answer,
        return_tensors="pt",
        truncation=True,
        max_length=512,
        padding=True,
    )

    with torch.no_grad():
        outputs = _hhem_model(**inputs)
        logits = outputs.logits
        # HHEM outputs: [inconsistent, consistent] logits
        probs = torch.softmax(logits, dim=-1)
        # Return probability of "consistent" class (index 1)
        consistent_prob = probs[0][1].item()

    return consistent_prob


def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Compute cosine similarity between two vectors."""
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))


def _split_sentences(text: str) -> list[str]:
    """Split text into sentences using basic regex."""
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    return [s.strip() for s in sentences if s.strip()]


def _score_with_embeddings(
    answer: str,
    context: str,
    model: SentenceTransformer,
    threshold: float = 0.5,
) -> float:
    """Score faithfulness using embedding cosine similarity fallback.

    Each answer sentence is compared against the concatenated context.
    Sentences with cosine similarity > threshold are considered faithful.

    Args:
        answer: The generated answer text.
        context: Concatenated context text.
        model: Pre-loaded SentenceTransformer model.
        threshold: Cosine similarity threshold for faithful classification.

    Returns:
        Fraction of answer sentences that are faithful (0.0-1.0).
    """
    sentences = _split_sentences(answer)
    if not sentences:
        return 1.0

    # Encode all sentences + context in one batch
    texts_to_encode = sentences + [context]
    embeddings = model.encode(texts_to_encode, convert_to_numpy=True)

    context_embedding = embeddings[-1]
    sentence_embeddings = embeddings[:-1]

    faithful_count = 0
    for sent_emb in sentence_embeddings:
        sim = _cosine_similarity(sent_emb, context_embedding)
        if sim > threshold:
            faithful_count += 1

    return faithful_count / len(sentences)


def compute_faithfulness(
    responses: list[QueryResponse | RefusalResponse],
    contexts: list[list[ScoredChunk]],
    model: SentenceTransformer | None = None,
) -> float:
    """Compute faithfulness score across all responses.

    Measures how well generated answers are grounded in the retrieved context.
    Uses HHEM classifier if available, otherwise falls back to embedding
    cosine similarity.

    Args:
        responses: List of query responses (QueryResponse or RefusalResponse).
        contexts: List of retrieved context chunks for each response.
        model: Optional SentenceTransformer model for embedding fallback.
            Required if HHEM is not available.

    Returns:
        Mean faithfulness score across all non-refusal responses (0.0-1.0).
        Returns 1.0 if no non-refusal responses exist.

    Raises:
        ValueError: If HHEM is unavailable and no embedding model is provided.
    """
    if not responses:
        return 1.0

    # Filter to only QueryResponse entries
    pairs: list[tuple[QueryResponse, list[ScoredChunk]]] = []
    for resp, ctx in zip(responses, contexts):
        if isinstance(resp, QueryResponse):
            pairs.append((resp, ctx))

    if not pairs:
        return 1.0

    use_hhem = _try_load_hhem()

    if not use_hhem and model is None:
        raise ValueError(
            "HHEM model unavailable and no SentenceTransformer model provided. "
            "Pass a model parameter for embedding fallback."
        )

    scores: list[float] = []
    for response, chunks in pairs:
        # Concatenate context chunk texts
        context_text = " ".join(chunk.chunk.text for chunk in chunks)
        if not context_text.strip():
            # No context to check against — can't assess faithfulness
            scores.append(0.0)
            continue

        if use_hhem:
            score = _score_with_hhem(response.answer, context_text)
        else:
            assert model is not None
            score = _score_with_embeddings(response.answer, context_text, model)

        scores.append(score)

    return float(np.mean(scores))


def compute_hallucination_rate(faithfulness_score: float) -> float:
    """Compute hallucination rate from faithfulness score.

    Hallucination rate is simply the complement of faithfulness:
    a faithfulness score of 0.8 means 20% hallucination rate.

    Args:
        faithfulness_score: Faithfulness score between 0.0 and 1.0.

    Returns:
        Hallucination rate between 0.0 and 1.0.
    """
    return 1.0 - faithfulness_score
