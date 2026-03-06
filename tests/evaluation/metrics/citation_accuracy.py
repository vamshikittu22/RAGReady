"""Citation accuracy metric for RAG evaluation.

Measures how accurately citations in the generated response link back to
real retrieved content. High citation accuracy means every citation
references a real document and real chunk text.

**Approach:**
- Fully deterministic — no embedding or classifier needed.
- For each QueryResponse (skip RefusalResponse):
  a. Every citation's document_name must exist in the known_documents set.
  b. Every citation's chunk_text must appear as a substring in at least one
     retrieved chunk's text (or vice versa — accounts for truncation).
- Citation Accuracy = valid_citations / total_citations.

**Limitations:**
- Substring matching may miss paraphrased citations.
- Does not check that the citation actually supports the specific claim.
- A citation can reference a valid chunk but be used out of context.

**Empty input handling:** Returns 1.0 if no citations exist (nothing to
be wrong about).
"""

from __future__ import annotations

from src.ragready.core.models import ScoredChunk
from src.ragready.generation.models import QueryResponse, RefusalResponse


def compute_citation_accuracy(
    responses: list[QueryResponse | RefusalResponse],
    retrieved_contexts: list[list[ScoredChunk]],
    known_documents: set[str],
) -> float:
    """Compute citation accuracy by validating citation references.

    Checks that each citation's document_name exists in the known document
    set and that the chunk_text appears in (or contains) at least one
    retrieved chunk's text.

    Args:
        responses: List of query responses (QueryResponse or RefusalResponse).
        retrieved_contexts: List of retrieved chunks for each response.
        known_documents: Set of known valid document names/filenames.

    Returns:
        Fraction of valid citations across all responses (0.0-1.0).
        Returns 1.0 if no citations exist.
    """
    if not responses:
        return 1.0

    total_citations = 0
    valid_citations = 0

    for response, chunks in zip(responses, retrieved_contexts):
        # Skip RefusalResponse entries
        if isinstance(response, RefusalResponse) or not isinstance(response, QueryResponse):
            continue

        for citation in response.citations:
            total_citations += 1

            # Check 1: document_name must be in known_documents
            if citation.document_name not in known_documents:
                continue

            # Check 2: chunk_text must appear in (or contain) a retrieved chunk
            chunk_text_valid = False
            for chunk in chunks:
                retrieved_text = chunk.chunk.text
                # Account for truncation: check both directions
                if (
                    citation.chunk_text in retrieved_text
                    or retrieved_text in citation.chunk_text
                ):
                    chunk_text_valid = True
                    break

            if chunk_text_valid:
                valid_citations += 1

    if total_citations == 0:
        return 1.0

    return valid_citations / total_citations
