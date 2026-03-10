# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-03-04)

**Core value:** Every generated answer must be grounded in retrieved evidence with verifiable citations — the system refuses to answer rather than hallucinate.
**Current focus:** Phase 5 (Fixes & V2 Features) — implementing streaming and bug fixes

## Current Position

Phase: 5 of 5 (Fixes & V2 Features) — IN PROGRESS
Plan: 1 of 1 in current phase (05-01 executing)
Status: Phase 5 in progress — streaming implementation complete, documentation in progress
Last activity: 2026-03-10 — Plan 05-01 (streaming + bug fixes)

Progress: [██████████] 100% (14/14 plans total, 1 in progress)

## Performance Metrics

**Velocity:**
- Total plans completed: 13
- Average duration: ~17min
- Total execution time: ~3h 50m

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 1 - Ingestion & Retrieval | 3/3 | ~123min | ~41min |
| 2 - Generation, API & Obs | 2/2 | ~18min | ~9min |
| 3 - Evaluation & CI/CD | 4/4 | ~19min | ~5min |
| 4 - Frontend & Portfolio | 3/3 | ~70min | ~23min |

**Recent Trend:**
- Last 5 plans: 03-04 (~2min), 04-01 (~45min), 04-02 (~15min), 04-03 (~10min)
- Trend: Frontend plans moderate duration; portfolio artifacts fast

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
- [03-03]: benchmark.py dual CLI/importable module — test_benchmark.py delegates, no duplication
- [03-03]: CI/local separation via @pytest.mark.ollama — 4 CI-safe + 3 local-only quality gates
- [03-03]: eval_metrics session fixture computes all metrics once, writes JSON report to reports/
- [03-04]: CI uses Python 3.12 (not 3.14) — GitHub Actions may lack 3.14 runners
- [03-04]: Sequential CI job chain: lint → unit → integration → evaluation for fast failure feedback
- [03-04]: Evaluation filter: -m "evaluation and not slow and not ollama" for CI-safe subset only

- [04-01]: Vite 7.3 + React 19.2 installed (latest stable, not Vite 6 as researched)
- [04-01]: shadcn/ui v4 uses base-nova style with Tailwind 4 CSS-first config (not New York)
- [04-01]: erasableSyntaxOnly enabled by Vite 7 — no parameter properties in class constructors
- [04-01]: verbatimModuleSyntax requires type keyword for type-only imports
- [04-01]: API client uses fetch wrappers with ApiError class, queryKeys factory pattern
- [04-02]: In-memory chat state via useState — no persistence, sufficient for portfolio demo
- [04-02]: 70/30 flex layout for chat/citations, responsive stacking on mobile
- [04-02]: AlertDialog for delete confirmation, drag-and-drop upload with file input fallback
- [04-03]: Static JSON for eval results — fetched from public/, replaceable by CI pipeline output
- [04-03]: Mermaid for architecture diagram — renders natively on GitHub, no image hosting
- [04-03]: Sample metric values as defaults — real values from running evaluate.py

- [05-01]: SSE streaming via /query/stream endpoint — tokens streamed as they're generated
- [05-01]: Frontend streaming toggle — users can enable/disable real-time response display
- [05-01]: LLMWrapper (renamed from LLMWithFallback) — correct class name in imports

### Pending Todos

None yet.

### Blockers/Concerns

- ~~[Research]: BM25 index is in-memory only (rank-bm25) — persistence strategy needs validation in Phase 1~~ RESOLVED in 01-02: pickle persistence validated with integration tests
- [Research]: Gemini Flash structured output reliability is the biggest unknown — needs hands-on testing in Phase 2
- [Research]: Ragas 0.4.x has breaking changes from tutorials — pin exact versions, use official docs only in Phase 3
- [01-02]: ChromaDB 1.5.2 requires venv-local pydantic v1 patch for Python 3.14 (PEP 749 lazy annotations)

## Session Continuity

Last session: 2026-03-10
Stopped at: Phase 5 (Fixes & V2 Features) — Plan 05-01 executing
Resume file: .planning/phases/05-fixes-and-v2-features/05-01-PLAN.md
