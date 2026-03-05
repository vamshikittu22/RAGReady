---
phase: 01-ingestion-retrieval
plan: 02
subsystem: ingestion, storage
tags: [langchain, chromadb, bm25, sentence-transformers, chunking, embeddings, pickle]

# Dependency graph
requires:
  - phase: 01-01
    provides: "Project scaffolding, core models (Chunk, Document, ScoredChunk), extractor registry"
provides:
  - "DocumentChunker with RecursiveCharacterTextSplitter (paragraph-first separators)"
  - "ChromaStore: ChromaDB PersistentClient with SentenceTransformer embedding"
  - "BM25Store: BM25Okapi sparse index with pickle persistence"
  - "DocumentStore: JSON manifest with cross-store sync verification"
  - "IngestionPipeline: extract → chunk → dual-index orchestrator"
  - "Metadata utilities: compute_content_hash, compute_document_id, detect_file_type"
affects: [01-03-retrieval, 02-generation, 02-api]

# Tech tracking
tech-stack:
  added: [langchain-text-splitters, chromadb, rank-bm25, sentence-transformers]
  patterns: [dual-indexing with atomic cleanup, pickle persistence for BM25, deterministic document IDs]

key-files:
  created:
    - src/ragready/ingestion/chunker.py
    - src/ragready/ingestion/metadata.py
    - src/ragready/ingestion/pipeline.py
    - src/ragready/storage/__init__.py
    - src/ragready/storage/chroma.py
    - src/ragready/storage/bm25_store.py
    - src/ragready/storage/document_store.py
    - tests/unit/test_chunker.py
    - tests/integration/__init__.py
    - tests/integration/test_ingestion_pipeline.py
  modified: []

key-decisions:
  - "Character-based chunking (512 chars, 50 overlap) rather than token-accurate splitting — sufficient for v1"
  - "BM25 persistence via pickle of chunk list, rebuild index on load — BM25Okapi cannot be incrementally updated"
  - "Atomic dual-indexing: if BM25 fails after ChromaDB succeeds, ChromaDB is cleaned up to prevent desync"
  - "Simple whitespace tokenization for BM25 — adequate for English text retrieval"
  - "Document manifest as JSON file for human readability and easy debugging"

patterns-established:
  - "Dual-index pattern: every write goes to both ChromaDB and BM25 with cleanup on partial failure"
  - "verify_sync() pattern: cross-store document ID comparison for desync detection"
  - "Factory function pattern: create_pipeline() constructs all dependencies from Settings"
  - "Deterministic ID pattern: document_id = SHA-256(filename:content_hash)[:16]"

# Metrics
duration: 63min
completed: 2026-03-05
---

# Phase 1 Plan 2: Chunking, Dual Storage, and Ingestion Pipeline Summary

**RecursiveCharacterTextSplitter chunking with dual-indexing into ChromaDB (dense) and BM25Okapi (sparse), orchestrated by IngestionPipeline with atomic cleanup and verify_sync**

## Performance

- **Duration:** ~63 min
- **Started:** 2026-03-05T13:05:46Z
- **Completed:** 2026-03-05T14:09:00Z
- **Tasks:** 2
- **Files created:** 10

## Accomplishments
- DocumentChunker splits text into ~512-char chunks with paragraph-first separators, producing Chunk objects with deterministic IDs, position metadata, page estimation, and content hashes
- ChromaStore wraps ChromaDB PersistentClient with SentenceTransformer embedding function, storing model name in collection metadata for mismatch detection
- BM25Store maintains BM25Okapi index with pickle persistence — survives restarts, handles corrupted files gracefully
- IngestionPipeline orchestrates extract → chunk → dual-index with atomic cleanup: if BM25 indexing fails, ChromaDB is rolled back
- DocumentStore JSON manifest enables verify_sync() to detect index desync across all three stores
- 53 total tests pass (28 unit chunker + 7 integration pipeline + 18 extractor tests from plan 01)

## Task Commits

Each task was committed atomically:

1. **Task 1: Document chunker and metadata utilities** - `18cee62` (feat)
2. **Task 2: Dual storage adapters and ingestion pipeline** - `d77ba67` (feat)

## Files Created/Modified
- `src/ragready/ingestion/chunker.py` - DocumentChunker class using RecursiveCharacterTextSplitter
- `src/ragready/ingestion/metadata.py` - compute_content_hash, compute_document_id, detect_file_type utilities
- `src/ragready/ingestion/pipeline.py` - IngestionPipeline orchestrator + create_pipeline() factory
- `src/ragready/storage/__init__.py` - Storage package init
- `src/ragready/storage/chroma.py` - ChromaStore: ChromaDB PersistentClient wrapper
- `src/ragready/storage/bm25_store.py` - BM25Store: BM25Okapi with pickle persistence
- `src/ragready/storage/document_store.py` - DocumentStore: JSON manifest with verify_sync()
- `tests/unit/test_chunker.py` - 28 unit tests for chunker and metadata
- `tests/integration/__init__.py` - Integration test package init
- `tests/integration/test_ingestion_pipeline.py` - 7 integration tests for full pipeline

## Decisions Made
- **Character-based chunking:** Used character count (512) rather than token-accurate splitting. RecursiveCharacterTextSplitter default is character-based, which maps roughly to tokens for English. Sufficient for v1; can add tiktoken length_function later.
- **BM25 persistence strategy:** Pickle the chunk list and rebuild BM25Okapi index on load. BM25Okapi is constructed once from the full corpus and cannot be incrementally updated, so rebuild is mandatory after every mutation.
- **Atomic dual-indexing:** If BM25 add fails after ChromaDB add succeeds, the pipeline deletes from ChromaDB before raising IndexingError. This prevents the index desync issue identified in Pitfall 2.
- **Simple whitespace tokenization:** BM25 tokenization uses `text.lower().split()` — no stemming or stopword removal. Adequate for v1 English retrieval.
- **JSON document manifest:** DocumentStore uses a JSON file rather than SQLite for simplicity and human readability. Easy to inspect/debug.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

- **ChromaDB + Python 3.14 compatibility:** ChromaDB 1.5.2 uses pydantic v1 internally, which breaks on Python 3.14 due to PEP 749 lazy annotations. This was resolved in a prior session by patching `.venv/Lib/site-packages/pydantic/v1/main.py` with annotationlib. The fix is venv-local and not tracked in git. All tests pass with the patched venv.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Ingestion pipeline is complete: files can be extracted, chunked, and dual-indexed
- Ready for Plan 01-03: Hybrid retrieval (dense + sparse search with RRF fusion)
- The BM25 persistence concern from STATE.md blockers is now resolved (pickle strategy validated with tests)

## Self-Check: PASSED

- All 10 created files verified on disk
- Commit `18cee62` (Task 1) verified in git log
- Commit `d77ba67` (Task 2) verified in git log
- 53/53 tests passing (unit + integration)

---
*Phase: 01-ingestion-retrieval*
*Completed: 2026-03-05*
