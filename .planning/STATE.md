# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-03-04)

**Core value:** Every generated answer must be grounded in retrieved evidence with verifiable citations — the system refuses to answer rather than hallucinate.
**Current focus:** Phase 3 in progress — Evaluation & CI/CD Quality Gates

## Current Position

Phase: 3 of 4 (Evaluation & CI/CD Quality Gates)
Plan: 2 of 4 in current phase (03-01, 03-02 done)
Status: Phase 3 in progress — 03-02 complete, ready for 03-03
Last activity: 2026-03-06 — Plan 03-02 completed (6 evaluation metric modules)

Progress: [███████░░░] 70% (7/10 plans)

## Performance Metrics

**Velocity:**
- Total plans completed: 7
- Average duration: ~23min
- Total execution time: ~2h 33m

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 1 - Ingestion & Retrieval | 3/3 | ~123min | ~41min |
| 2 - Generation, API & Obs | 2/2 | ~18min | ~9min |
| 3 - Evaluation & CI/CD | 2/4 | ~12min | ~6min |

**Recent Trend:**
- Last 5 plans: 01-03 (~35min), 02-01 (~12min), 02-02 (~6min), 03-01 (~8min), 03-02 (~4min)
- Trend: Fast metric/fixture plans; evaluation modules very fast (pure functions)

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
- [02-01]: LLMWithFallback.with_structured_output() propagates schema to both primary and fallback LLMs
- [02-01]: Pre-LLM refusal gate checks max retrieval score against confidence_threshold before invoking LLM
- [02-01]: Separate empty-chunks vs low-score refusal paths for clearer error messages
- [02-02]: Sync def for /query route — FastAPI threadpool avoids blocking event loop with LangChain sync .invoke()
- [02-02]: Phoenix tracing uses lazy imports for graceful degradation without phoenix packages
- [02-02]: DI via lru_cache singletons (get_settings/get_pipeline/get_rag_chain)
- [03-01]: 51 golden entries (36 factual, 5 comparative, 10 refusal) — exceeds 50 minimum
- [03-01]: Synthetic response generation concatenates top-3 chunk texts — tests measurement pipeline not LLM
- [03-01]: Session-scoped fixtures use tmp_path_factory for expensive pipeline/retrieval operations
- [03-02]: HHEM with embedding fallback for faithfulness — no LLM judge, classifier or cosine similarity only
- [03-02]: Cosine thresholds: 0.5 faithfulness, 0.7 context recall, 0.3 context precision
- [03-02]: Deterministic refusal accuracy (isinstance) and citation accuracy (substring + set membership)
- [03-02]: All metrics return 1.0 for empty inputs — nothing to measure = nothing wrong

### Pending Todos

None yet.

### Blockers/Concerns

- ~~[Research]: BM25 index is in-memory only (rank-bm25) — persistence strategy needs validation in Phase 1~~ RESOLVED in 01-02: pickle persistence validated with integration tests
- [Research]: Gemini Flash structured output reliability is the biggest unknown — needs hands-on testing in Phase 2
- [Research]: Ragas 0.4.x has breaking changes from tutorials — pin exact versions, use official docs only in Phase 3
- [01-02]: ChromaDB 1.5.2 requires venv-local pydantic v1 patch for Python 3.14 (PEP 749 lazy annotations)

## Session Continuity

Last session: 2026-03-06
Stopped at: Completed 03-02-PLAN.md — 6 evaluation metric modules
Resume file: .planning/phases/03-evaluation-cicd-quality-gates/03-02-SUMMARY.md
