---
phase: 02-generation-api-observability
plan: 02
subsystem: api
tags: [fastapi, rest-api, swagger, cors, middleware, structlog, phoenix, opentelemetry, langchain-instrumentation]

# Dependency graph
requires:
  - phase: 02-generation-api-observability
    plan: 01
    provides: "RAGChain, QueryResponse, RefusalResponse, create_rag_chain, LLMWithFallback"
  - phase: 01-ingestion-retrieval
    provides: "IngestionPipeline, HybridRetriever, create_pipeline, create_retriever, ChromaStore, BM25Store"
provides:
  - "FastAPI app factory (create_app) with CORS, latency middleware, route registration"
  - "POST /query endpoint returning QueryResponse or RefusalResponse"
  - "POST /documents/upload, GET /documents, DELETE /documents/{id} for document CRUD"
  - "GET /health endpoint with system status"
  - "Dependency injection (get_settings, get_pipeline, get_rag_chain) via lru_cache"
  - "LatencyLoggingMiddleware logging method, path, status, duration_ms per request"
  - "Phoenix OTEL tracing setup with LangChain auto-instrumentation"
affects: [03-evaluation, 04-frontend]

# Tech tracking
tech-stack:
  added: [fastapi, uvicorn, structlog-middleware]
  patterns: [app-factory, dependency-injection-lru-cache, latency-middleware, lazy-tracing-import, async-file-upload]

key-files:
  created:
    - src/ragready/api/__init__.py
    - src/ragready/api/app.py
    - src/ragready/api/dependencies.py
    - src/ragready/api/middleware.py
    - src/ragready/api/routes/__init__.py
    - src/ragready/api/routes/query.py
    - src/ragready/api/routes/documents.py
    - src/ragready/api/routes/health.py
    - src/ragready/observability/__init__.py
    - src/ragready/observability/tracing.py
    - tests/unit/test_api_routes.py
  modified:
    - .env.example

key-decisions:
  - "Sync def for /query route (FastAPI threadpool) to avoid blocking event loop with LangChain sync .invoke()"
  - "pipeline.delete() returns bool, route uses 404 on False rather than catching DocumentNotFoundError"
  - "Phoenix tracing uses lazy imports inside setup_tracing() for graceful degradation"

patterns-established:
  - "App factory pattern: create_app() returns fully-wired FastAPI instance"
  - "DI via lru_cache: get_settings/get_pipeline/get_rag_chain as singleton providers"
  - "TestClient with dependency_overrides for API testing without real services"
  - "File upload with temp file pattern: save → ingest → cleanup in finally block"

# Metrics
duration: 6min
completed: 2026-03-06
---

# Phase 2 Plan 2: API & Observability Summary

**FastAPI REST API with 5 endpoint groups (query, upload, list, delete, health), latency middleware, dependency injection, and Phoenix OTEL tracing with LangChain auto-instrumentation**

## Performance

- **Duration:** 6 min
- **Started:** 2026-03-06T06:04:19Z
- **Completed:** 2026-03-06T06:10:28Z
- **Tasks:** 2
- **Files modified:** 12

## Accomplishments
- Built complete FastAPI REST API with app factory pattern, CORS, and Swagger UI
- Implemented all 5 endpoint groups: POST /query, POST /documents/upload, GET /documents, DELETE /documents/{id}, GET /health
- Added latency logging middleware logging method, path, status, and duration_ms for every request
- Created Phoenix OTEL tracing setup with LangChain auto-instrumentation (non-blocking, optional)
- Added 9 API tests with mocked dependencies, 98 total tests passing

## Task Commits

Each task was committed atomically:

1. **Task 1: FastAPI app, dependency injection, middleware, and all route handlers** - `55684cc` (feat)
2. **Task 2: Phoenix observability tracing setup** - `711751b` (feat)

## Files Created/Modified
- `src/ragready/api/__init__.py` — Package init exporting create_app
- `src/ragready/api/app.py` — FastAPI app factory with CORS, middleware, routes, and lifespan tracing
- `src/ragready/api/dependencies.py` — DI providers: get_settings, get_pipeline, get_rag_chain
- `src/ragready/api/middleware.py` — LatencyLoggingMiddleware using structlog
- `src/ragready/api/routes/__init__.py` — Routes package init
- `src/ragready/api/routes/query.py` — POST /query with QueryResponse/RefusalResponse
- `src/ragready/api/routes/documents.py` — Upload, list, delete document endpoints
- `src/ragready/api/routes/health.py` — GET /health with system status
- `src/ragready/observability/__init__.py` — Package init exporting setup_tracing
- `src/ragready/observability/tracing.py` — Phoenix OTEL + LangChain instrumentation setup
- `tests/unit/test_api_routes.py` — 9 API endpoint tests with mocked dependencies
- `.env.example` — Added LLM, Ollama, and Phoenix configuration entries

## Decisions Made
- Used sync `def` (not `async def`) for /query route since LangChain's `.invoke()` is synchronous — FastAPI automatically runs sync handlers in a threadpool to avoid blocking the event loop
- Used `pipeline.delete()` boolean return value rather than catching DocumentNotFoundError — the pipeline already returns False for missing docs
- Phoenix tracing uses lazy imports inside the function body so the app works even without phoenix packages installed

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required. The API endpoints use existing Settings from .env (Google API key, Ollama URL). Phoenix tracing is disabled by default.

## Next Phase Readiness
- Phase 2 complete — all generation pipeline + API + observability delivered
- Server runnable via `uvicorn ragready.api.app:create_app --factory`
- Swagger UI at /docs shows all endpoints with request/response schemas
- Ready for Phase 3: Evaluation & CI

## Self-Check: PASSED

- All 11 created files verified on disk
- Both task commits (55684cc, 711751b) verified in git log
- 98/98 tests passing

---
*Phase: 02-generation-api-observability*
*Completed: 2026-03-06*
