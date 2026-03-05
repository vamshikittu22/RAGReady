# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-03-04)

**Core value:** Every generated answer must be grounded in retrieved evidence with verifiable citations — the system refuses to answer rather than hallucinate.
**Current focus:** Phase 1 — Ingestion & Retrieval Pipeline

## Current Position

Phase: 1 of 4 (Ingestion & Retrieval Pipeline) — COMPLETE
Plan: 3 of 3 in current phase (all done)
Status: Phase 1 complete, ready for Phase 2
Last activity: 2026-03-05 — Plan 01-03 completed (Phase 1 done)

Progress: [███░░░░░░░] 30% (3/10 plans)

## Performance Metrics

**Velocity:**
- Total plans completed: 3
- Average duration: ~41min
- Total execution time: ~2 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 1 - Ingestion & Retrieval | 3/3 | ~123min | ~41min |

**Recent Trend:**
- Last 5 plans: 01-01 (~25min), 01-02 (~63min), 01-03 (~35min)
- Trend: Phase 1 complete. Retrieval plan faster due to simpler components (thin wrappers + RRF algorithm)

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
- [01-03]: No cross-encoder reranking in Phase 1 — deferred to v2, pipeline is dense+sparse→RRF→top-k
- [01-03]: RRF constant k=60 (Cormack et al., 2009 standard default), configurable via Settings
- [01-03]: IngestionPipeline gains public accessors for chroma/bm25/doc_store to support retrieval layer wiring

### Pending Todos

None yet.

### Blockers/Concerns

- ~~[Research]: BM25 index is in-memory only (rank-bm25) — persistence strategy needs validation in Phase 1~~ RESOLVED in 01-02: pickle persistence validated with integration tests
- [Research]: Gemini Flash structured output reliability is the biggest unknown — needs hands-on testing in Phase 2
- [Research]: Ragas 0.4.x has breaking changes from tutorials — pin exact versions, use official docs only in Phase 3
- [01-02]: ChromaDB 1.5.2 requires venv-local pydantic v1 patch for Python 3.14 (PEP 749 lazy annotations)

## Session Continuity

Last session: 2026-03-05
Stopped at: Completed 01-03-PLAN.md — Phase 1 complete, ready for Phase 2
Resume file: .planning/phases/01-ingestion-retrieval/01-03-SUMMARY.md
