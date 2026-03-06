---
phase: 03-evaluation-cicd-quality-gates
plan: 02
subsystem: testing
tags: [evaluation, metrics, faithfulness, relevancy, context-recall, context-precision, refusal-accuracy, citation-accuracy, sentence-transformers, hhem, cosine-similarity]

# Dependency graph
requires:
  - phase: 01-ingestion-retrieval
    provides: "ScoredChunk, Chunk, Document models for metric inputs"
  - phase: 02-generation-api-observability
    provides: "QueryResponse, RefusalResponse, Citation models for metric inputs"
  - phase: 03-evaluation-cicd-quality-gates (03-01)
    provides: "Golden dataset, test fixtures, embedding_model conftest fixture"
provides:
  - "6 evaluation metric modules (compute_* functions)"
  - "Faithfulness via HHEM classifier with embedding cosine similarity fallback"
  - "Answer relevancy via embedding cosine similarity"
  - "Context recall and precision via embedding cosine similarity"
  - "Refusal accuracy and citation accuracy via deterministic checks"
  - "Hallucination rate as 1 - faithfulness complement"
affects: [03-03, 03-04, 04-02]

# Tech tracking
tech-stack:
  added: [vectara/hallucination_evaluation_model (HHEM), transformers (optional)]
  patterns: [layered-fallback (HHEM→embedding→cosine), deterministic-metrics, classifier-based-faithfulness, embedding-cosine-similarity]

key-files:
  created:
    - tests/evaluation/metrics/faithfulness.py
    - tests/evaluation/metrics/relevancy.py
    - tests/evaluation/metrics/context_recall.py
    - tests/evaluation/metrics/context_precision.py
    - tests/evaluation/metrics/refusal_accuracy.py
    - tests/evaluation/metrics/citation_accuracy.py
  modified: []

key-decisions:
  - "HHEM with embedding fallback for faithfulness — no LLM judge needed"
  - "Cosine similarity thresholds: 0.5 for faithfulness, 0.7 for context recall, 0.3 for context precision"
  - "Deterministic metrics for refusal and citation accuracy — no model needed"
  - "All metrics return 1.0 for empty inputs (nothing wrong if nothing to check)"

patterns-established:
  - "Metric signature pattern: compute_*(inputs) -> float (0.0-1.0)"
  - "Skip RefusalResponse entries for answer-quality metrics"
  - "Embedding model passed as parameter (from conftest fixture), not loaded per-module"
  - "Bidirectional substring match for citation chunk_text validation"

# Metrics
duration: 4min
completed: 2026-03-06
---

# Phase 3 Plan 2: Evaluation Metrics Summary

**6 RAG evaluation metrics — faithfulness (HHEM/embedding fallback), relevancy, context recall/precision (embedding cosine similarity), refusal accuracy and citation accuracy (deterministic) — all LLM-judge-free**

## Performance

- **Duration:** ~4 min
- **Started:** 2026-03-06T07:48:00Z
- **Completed:** 2026-03-06T07:51:00Z
- **Tasks:** 2
- **Files created:** 6

## Accomplishments
- Implemented faithfulness metric with 3-layer fallback: Ragas HHEM → transformers HHEM → embedding cosine similarity
- Built 4 embedding-based metrics (faithfulness fallback, relevancy, context recall, context precision) using SentenceTransformer
- Created 2 fully deterministic metrics (refusal accuracy, citation accuracy) requiring zero ML models
- All 6 metrics produce float scores 0.0-1.0 with graceful empty-input handling

## Task Commits

Each task was committed atomically:

1. **Task 1: Faithfulness, answer relevancy, and hallucination metrics** - `d75e06a` (feat)
2. **Task 2: Context recall, context precision, refusal accuracy, and citation accuracy metrics** - `df9a56a` (feat)

## Files Created/Modified
- `tests/evaluation/metrics/faithfulness.py` - HHEM classifier → embedding cosine fallback, compute_faithfulness + compute_hallucination_rate
- `tests/evaluation/metrics/relevancy.py` - Embedding cosine similarity between question and answer, compute_answer_relevancy
- `tests/evaluation/metrics/context_recall.py` - Embedding similarity check of expected vs retrieved contexts (threshold 0.7), compute_context_recall
- `tests/evaluation/metrics/context_precision.py` - Embedding similarity check of question vs retrieved chunks (threshold 0.3), compute_context_precision
- `tests/evaluation/metrics/refusal_accuracy.py` - Deterministic isinstance checks for correct refusal/answer behavior, compute_refusal_accuracy
- `tests/evaluation/metrics/citation_accuracy.py` - Deterministic document name + chunk text substring validation, compute_citation_accuracy

## Decisions Made
- **HHEM with embedding fallback for faithfulness:** Uses Vectara HHEM-2.1-Open as primary classifier, falls back to embedding cosine similarity when HHEM unavailable. No LLM judge needed since system only has 3B parameter local model.
- **Cosine similarity thresholds:** 0.5 for faithfulness sentence grounding, 0.7 for context recall (strict — expected context should be very similar), 0.3 for context precision (lenient — general topical relevance).
- **Deterministic metrics for refusal and citation:** Refusal uses isinstance checks against RefusalResponse/QueryResponse. Citation uses document name set membership + bidirectional substring matching.
- **Empty input → 1.0:** All metrics return 1.0 when no applicable entries exist (nothing to measure = nothing wrong).

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- All 6 metric modules ready for integration in 03-03 quality gate tests and benchmark scripts
- Metrics accept pre-loaded SentenceTransformer model from conftest fixtures (established in 03-01)
- Ready for 03-03: quality gate tests, benchmark tests, CLI scripts

## Self-Check: PASSED

- All 6 metric files verified on disk
- __init__.py exists
- 2 commits found for 03-02

---
*Phase: 03-evaluation-cicd-quality-gates*
*Completed: 2026-03-06*
