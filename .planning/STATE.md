# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-03-04)

**Core value:** Every generated answer must be grounded in retrieved evidence with verifiable citations — the system refuses to answer rather than hallucinate.
**Current focus:** Phase 1 — Ingestion & Retrieval Pipeline

## Current Position

Phase: 1 of 4 (Ingestion & Retrieval Pipeline)
Plan: 2 of 3 in current phase
Status: Executing phase 1
Last activity: 2026-03-05 — Plan 01-02 completed

Progress: [██░░░░░░░░] 20% (2/10 plans)

## Performance Metrics

**Velocity:**
- Total plans completed: 2
- Average duration: ~44min
- Total execution time: ~1.5 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 1 - Ingestion & Retrieval | 2/3 | ~88min | ~44min |

**Recent Trend:**
- Last 5 plans: 01-01 (~25min), 01-02 (~63min)
- Trend: Second plan complete, integration tests take longer

*Updated after each plan completion*

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- [Roadmap]: 4-phase structure following data dependency chain (Ingestion+Retrieval → Generation+API+Obs → Eval+CI → Frontend+Portfolio)
- [Roadmap]: Cross-encoder reranking deferred to v2, not included in retrieval phase
- [Roadmap]: Observability (Arize Phoenix) grouped with Generation+API in Phase 2 since tracing wraps the query pipeline
- [01-01]: Switched build system from hatchling to setuptools — hatchling fails on Python 3.14.2
- [01-01]: Markdown extractor returns raw text (not HTML-converted) to preserve section headers for chunking
- [01-01]: Chunk.generate_id uses SHA-256 of doc_id:chunk_index:text[:100] truncated to 16 hex chars
- [01-01]: Protocol-based extractor interface (structural subtyping, no inheritance required)
- [01-02]: Character-based chunking (512 chars, 50 overlap) — sufficient for v1, can add tiktoken later
- [01-02]: BM25 persistence via pickle of chunk list — rebuild index on load since BM25Okapi is immutable
- [01-02]: Atomic dual-indexing: BM25 failure triggers ChromaDB cleanup to prevent desync
- [01-02]: JSON document manifest for human readability; verify_sync() for cross-store consistency

### Pending Todos

None yet.

### Blockers/Concerns

- ~~[Research]: BM25 index is in-memory only (rank-bm25) — persistence strategy needs validation in Phase 1~~ RESOLVED in 01-02: pickle persistence validated with integration tests
- [Research]: Gemini Flash structured output reliability is the biggest unknown — needs hands-on testing in Phase 2
- [Research]: Ragas 0.4.x has breaking changes from tutorials — pin exact versions, use official docs only in Phase 3
- [01-02]: ChromaDB 1.5.2 requires venv-local pydantic v1 patch for Python 3.14 (PEP 749 lazy annotations)

## Session Continuity

Last session: 2026-03-05
Stopped at: Completed 01-02-PLAN.md — ready to plan 01-03
Resume file: .planning/phases/01-ingestion-retrieval/01-02-SUMMARY.md
