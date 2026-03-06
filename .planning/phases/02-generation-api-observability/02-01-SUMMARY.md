---
phase: 02-generation-api-observability
plan: 01
subsystem: generation
tags: [langchain, gemini, ollama, pydantic, structured-output, rag-chain, citation]

# Dependency graph
requires:
  - phase: 01-ingestion-retrieval
    provides: "HybridRetriever, ScoredChunk, Chunk, ChunkMetadata models, Settings"
provides:
  - "QueryResponse, Citation, RefusalResponse Pydantic models for structured LLM output"
  - "LLMWithFallback with Gemini primary + Qwen/Ollama fallback"
  - "RAGChain.query() pipeline: retrieve → refusal check → prompt → generate → return"
  - "create_rag_chain() factory for wiring retriever + settings"
  - "build_prompt() for grounding prompt construction with chunk metadata"
affects: [02-02-api-observability, 03-evaluation]

# Tech tracking
tech-stack:
  added: [langchain-ollama, openinference-instrumentation-langchain, arize-phoenix-otel]
  patterns: [LLM-with-fallback, pre-LLM-refusal-gate, structured-output-propagation, grounding-prompt]

key-files:
  created:
    - src/ragready/generation/__init__.py
    - src/ragready/generation/models.py
    - src/ragready/generation/llm.py
    - src/ragready/generation/prompts.py
    - src/ragready/generation/chain.py
    - tests/unit/test_generation_models.py
    - tests/unit/test_generation_chain.py
  modified:
    - pyproject.toml
    - src/ragready/core/config.py
    - src/ragready/core/exceptions.py

key-decisions:
  - "LLMWithFallback.with_structured_output() propagates schema to both primary and fallback LLMs"
  - "Pre-LLM refusal gate checks max retrieval score against confidence_threshold before invoking LLM"
  - "Separate empty-chunks vs low-score refusal paths for clearer error messages"

patterns-established:
  - "LLM fallback pattern: try primary, catch any Exception, try fallback, raise LLMUnavailableError if both fail"
  - "Structured output propagation: with_structured_output() returns new wrapper with schema-bound LLMs"
  - "Pre-LLM refusal gate: check retrieval quality before spending tokens on generation"

# Metrics
duration: 12min
completed: 2026-03-06
---

# Phase 2 Plan 1: Generation Pipeline Summary

**Citation-enforced RAG chain with Gemini+Qwen fallback, structured Pydantic output models, grounding prompts, and pre-LLM refusal gating**

## Performance

- **Duration:** 12 min
- **Started:** 2026-03-06T00:00:00Z
- **Completed:** 2026-03-06T00:12:00Z
- **Tasks:** 2
- **Files modified:** 10

## Accomplishments
- Built complete generation pipeline: QueryResponse, Citation, RefusalResponse models with Pydantic v2 field constraints
- Implemented LLMWithFallback with Gemini Flash primary + Qwen/Ollama fallback and structured output propagation
- Created RAGChain.query() orchestrating retrieve → refusal check → prompt → generate → return
- Added pre-LLM refusal gate that saves tokens by refusing queries with insufficient retrieval evidence
- Extended Settings with LLM, Ollama, and Phoenix observability configuration fields
- Added 20 unit tests (10 model validation + 10 chain logic with mocks) — all 89 tests pass

## Task Commits

Each task was committed atomically:

1. **Task 1: Generation response models, config extensions, and LLM factory with fallback** - `0efc24a` (feat)
2. **Task 2: Grounding prompts and RAG generation chain with refusal logic** - `1d21935` (feat)

## Files Created/Modified
- `src/ragready/generation/__init__.py` — Package init exporting all public interfaces
- `src/ragready/generation/models.py` — QueryResponse, Citation, RefusalResponse Pydantic models
- `src/ragready/generation/llm.py` — LLMWithFallback class with Gemini+Qwen and structured output
- `src/ragready/generation/prompts.py` — Grounding system prompt and build_prompt() message builder
- `src/ragready/generation/chain.py` — RAGChain with query pipeline and create_rag_chain() factory
- `tests/unit/test_generation_models.py` — 10 model validation tests
- `tests/unit/test_generation_chain.py` — 10 chain/prompt tests with mocked LLM calls
- `pyproject.toml` — Added langchain-ollama, openinference-instrumentation-langchain, arize-phoenix-otel
- `src/ragready/core/config.py` — Extended Settings with LLM, Ollama, Phoenix fields
- `src/ragready/core/exceptions.py` — Added GenerationError, LLMUnavailableError

## Decisions Made
- LLMWithFallback.with_structured_output() creates a new wrapper with schema-bound LLMs rather than modifying in place — preserves immutability and allows different schemas per query
- Pre-LLM refusal gate uses separate code paths for empty chunks vs low-score chunks for clearer error messages and logging
- Gemini uses method="json_schema" for structured output while Ollama uses default method — Gemini-specific JSON schema support is more reliable

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required for the generation pipeline itself. Google API key (RAGREADY_GOOGLE_API_KEY) and Ollama are configured at runtime, documented in plan frontmatter user_setup.

## Next Phase Readiness
- Generation pipeline complete and self-contained — ready for Plan 02 to build FastAPI endpoints and Phoenix observability
- All exports (RAGChain, create_rag_chain, QueryResponse, etc.) available via `ragready.generation`
- 89 tests pass with zero regressions

## Self-Check: PASSED

- All 7 created files verified on disk
- Both task commits (0efc24a, 1d21935) verified in git log
- 89/89 tests passing

---
*Phase: 02-generation-api-observability*
*Completed: 2026-03-06*
