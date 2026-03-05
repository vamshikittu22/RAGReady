---
phase: 01-ingestion-retrieval
plan: 01
subsystem: ingestion
tags: [pymupdf, beautifulsoup4, pydantic-settings, extractors, python-packaging, setuptools]

# Dependency graph
requires:
  - phase: none
    provides: "First plan — no prior dependencies"
provides:
  - "Installable ragready Python package with src-layout"
  - "Pydantic Settings configuration system (env-based)"
  - "Domain models: Chunk, Document, ScoredChunk, ChunkMetadata"
  - "Custom exception hierarchy (RAGReadyError base)"
  - "ExtractorRegistry with 4 extractors (PDF, Markdown, HTML, Plaintext)"
  - "BaseExtractor protocol for future extractor additions"
affects: [01-02, 01-03, 02-01, 02-02]

# Tech tracking
tech-stack:
  added: [setuptools, pydantic>=2.12.0, pydantic-settings, PyMuPDF>=1.27.0, beautifulsoup4>=4.12.0, markdown>=3.5, sentence-transformers>=5.2.0, chromadb>=1.5.0, langchain-core, langchain-google-genai, langchain-community, fastapi, uvicorn, rank-bm25, tenacity, tiktoken, structlog, httpx, numpy, aiofiles, pytest, pytest-asyncio, pytest-cov, ruff, mypy]
  patterns: [src-layout packaging, Protocol-based extractor interface, ExtractorRegistry pattern, pydantic BaseSettings with env_prefix, deterministic ID generation via SHA-256]

key-files:
  created:
    - pyproject.toml
    - .gitignore
    - .env.example
    - src/ragready/__init__.py
    - src/ragready/core/config.py
    - src/ragready/core/models.py
    - src/ragready/core/exceptions.py
    - src/ragready/ingestion/extractors/base.py
    - src/ragready/ingestion/extractors/pdf.py
    - src/ragready/ingestion/extractors/markdown.py
    - src/ragready/ingestion/extractors/html.py
    - src/ragready/ingestion/extractors/plaintext.py
    - tests/unit/test_extractors.py
  modified: []

key-decisions:
  - "Switched build system from hatchling to setuptools — hatchling fails to import on Python 3.14.2"
  - "Markdown extractor returns raw markdown text (not HTML-converted) — preserves section headers for downstream chunking"
  - "Chunk.generate_id uses SHA-256 of doc_id:chunk_index:text[:100] truncated to 16 hex chars for deterministic IDs"
  - "PlaintextExtractor uses UTF-8 with latin-1 fallback for broad encoding compatibility"

patterns-established:
  - "Protocol-based interface: BaseExtractor defines extract() + supported_extensions, concrete classes implement without inheritance"
  - "Registry pattern: ExtractorRegistry maps file extensions to extractor instances with get_extractor() dispatch"
  - "ExtractedDocument as uniform return type: text + metadata dict from all extractors"
  - "Pydantic Settings with RAGREADY_ env prefix for all configuration"
  - "Custom exception hierarchy rooted at RAGReadyError for typed error handling"

# Metrics
duration: ~25min
completed: 2026-03-05
---

# Phase 1 Plan 01: Project Foundation & Document Extractors Summary

**Installable Python package with Pydantic config, domain models, and 4 document text extractors (PDF/MD/HTML/TXT) via Protocol-based registry — 18 tests passing**

## Performance

- **Duration:** ~25 min
- **Started:** 2026-03-05T06:10:00Z
- **Completed:** 2026-03-05T06:35:00Z
- **Tasks:** 2
- **Files modified:** 18

## Accomplishments
- Fully installable `ragready` package with src-layout and all production + dev dependencies resolved on Python 3.14.2
- Pydantic Settings configuration system loading from environment variables with sensible defaults (chunk_size=512, rrf_k=60, final_top_k=5)
- Domain models (Chunk, Document, ScoredChunk, ChunkMetadata) with deterministic chunk ID generation
- 4 document extractors (PDF via PyMuPDF, Markdown, HTML via BeautifulSoup4, Plaintext) behind ExtractorRegistry
- 18 unit tests covering all extractors, registry dispatch, error handling, and encoding fallback

## Task Commits

Each task was committed atomically:

1. **Task 1: Project scaffolding, dependencies, and core module** - `b8b3b55` (feat)
2. **Task 2: Document text extractors for PDF, Markdown, HTML, and plaintext** - `0eed268` (feat)

## Files Created/Modified
- `pyproject.toml` — Project metadata, all dependencies (setuptools build system)
- `.gitignore` — Python defaults + data/index exclusions
- `.env.example` — All RAGREADY_ env vars documented with defaults
- `src/ragready/__init__.py` — Package root with version
- `src/ragready/core/config.py` — Settings(BaseSettings) with env_prefix="RAGREADY_"
- `src/ragready/core/models.py` — Chunk, Document, ScoredChunk, ChunkMetadata models
- `src/ragready/core/exceptions.py` — RAGReadyError hierarchy (Extraction, Chunking, Indexing, Retrieval, DocumentNotFound)
- `src/ragready/ingestion/extractors/base.py` — ExtractedDocument, BaseExtractor Protocol, ExtractorRegistry
- `src/ragready/ingestion/extractors/pdf.py` — PDFExtractor using PyMuPDF (fitz)
- `src/ragready/ingestion/extractors/markdown.py` — MarkdownExtractor (raw text, preserves headers)
- `src/ragready/ingestion/extractors/html.py` — HTMLExtractor (strips script/style/nav/footer/header tags)
- `src/ragready/ingestion/extractors/plaintext.py` — PlaintextExtractor (UTF-8 + latin-1 fallback)
- `src/ragready/ingestion/extractors/__init__.py` — create_default_registry() factory
- `tests/unit/test_extractors.py` — 18 tests for all extractors + registry

## Decisions Made
- **Setuptools over hatchling**: Hatchling's build backend cannot be imported on Python 3.14.2 (`Cannot import 'hatchling.backends'`). Setuptools works reliably. This is a build-time-only concern and doesn't affect the package interface.
- **Raw markdown preservation**: MarkdownExtractor returns raw markdown text rather than converting to HTML or stripping formatting, because section headers (#, ##) are valuable signals for the downstream chunking engine.
- **Deterministic chunk IDs**: `Chunk.generate_id()` hashes `{doc_id}:{chunk_index}:{text[:100]}` with SHA-256, truncated to 16 hex chars. Prevents duplicate chunks across re-ingestion (addresses Pitfall 15 from research).
- **Protocol over ABC**: Used `typing.Protocol` for BaseExtractor instead of ABC, enabling structural subtyping — extractors don't need to inherit, just implement the interface.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Switched build system from hatchling to setuptools**
- **Found during:** Task 1 (project scaffolding)
- **Issue:** `pip install -e ".[dev]"` failed with `Cannot import 'hatchling.backends'` on Python 3.14.2 — hatchling doesn't yet support Python 3.14
- **Fix:** Changed `[build-system]` in pyproject.toml from hatchling to setuptools with `setuptools>=75.0.0` and `setuptools-scm>=8.0`
- **Files modified:** pyproject.toml
- **Verification:** `pip install -e ".[dev]"` succeeds, all imports work
- **Committed in:** b8b3b55 (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (Rule 3 - blocking)
**Impact on plan:** Minimal — setuptools is a standard build backend, no functional difference for the package.

## Issues Encountered
- Python 3.14.2 is bleeding-edge; `pip` is not directly on PATH — must use `.venv/Scripts/python.exe -m pip` or `.venv/Scripts/pip.exe`. Resolved by using venv consistently.
- CRLF line ending warnings from Git on Windows — cosmetic only, no impact on functionality.

## User Setup Required
None - no external service configuration required.

## Next Plan Readiness
- Package foundation complete: all domain models, config, and extractors ready for Plan 01-02
- Plan 01-02 (chunking engine + dual storage) can import from `ragready.core.models`, `ragready.core.config`, and `ragready.ingestion.extractors`
- ExtractorRegistry provides `create_default_registry()` for the ingestion pipeline to use
- No blockers for proceeding

## Self-Check: PASSED

- All 14 key files: FOUND
- Commit b8b3b55 (Task 1): FOUND
- Commit 0eed268 (Task 2): FOUND
- All 18 tests: PASSING

---
*Phase: 01-ingestion-retrieval, Plan: 01*
*Completed: 2026-03-05*
