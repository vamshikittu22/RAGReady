"""Refusal accuracy metric for RAG evaluation.

Measures how accurately the system refuses to answer when it should (and
answers when it should). A system with high refusal accuracy correctly
identifies when evidence is insufficient and refuses rather than hallucinating.

**Approach:**
- Fully deterministic — no embedding or classifier needed.
- For each golden entry:
  - If should_refuse=True: correct if response is a RefusalResponse.
  - If should_refuse=False: correct if response is a QueryResponse.
- Refusal Accuracy = (correct responses) / (total responses).

**Limitations:**
- Binary classification only — does not evaluate refusal reason quality.
- Depends entirely on the golden dataset's should_refuse labels.
- Does not measure partial refusal (answering with low confidence).

**Empty input handling:** Returns 1.0 if no entries to check.
"""

from __future__ import annotations

from src.ragready.generation.models import QueryResponse, RefusalResponse


def compute_refusal_accuracy(
    golden_entries: list[dict],
    responses: list[QueryResponse | RefusalResponse],
) -> float:
    """Compute refusal accuracy by comparing expected vs actual refusal behavior.

    Uses isinstance checks to determine whether the system correctly refused
    or answered for each golden entry based on the should_refuse flag.

    Args:
        golden_entries: List of golden dataset entries. Each entry is a dict
            with a 'should_refuse' (bool) field.
        responses: List of query responses (QueryResponse or RefusalResponse).

    Returns:
        Fraction of correct refusal/answer decisions (0.0-1.0).
        Returns 1.0 if no entries to check.
    """
    if not golden_entries or not responses:
        return 1.0

    correct = 0
    total = 0

    for entry, response in zip(golden_entries, responses):
        should_refuse = entry.get("should_refuse", False)
        total += 1

        if should_refuse:
            # Should refuse: correct if response is RefusalResponse
            if isinstance(response, RefusalResponse) or getattr(response, "refused", False):
                correct += 1
        else:
            # Should answer: correct if response is QueryResponse (not RefusalResponse)
            if isinstance(response, QueryResponse) and not getattr(response, "refused", False):
                correct += 1

    if total == 0:
        return 1.0

    return correct / total
