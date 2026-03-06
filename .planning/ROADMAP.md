# Roadmap: RAGReady

## Overview

RAGReady follows a strict data dependency chain: documents must be ingested and indexed before retrieval can work, retrieval must produce chunks before generation can cite them, and the full pipeline must exist before evaluation can measure it. This roadmap compresses 53 requirements into 4 phases that each deliver a testable capability, ending with the frontend UI and portfolio artifacts that showcase the complete system.

## Phases

- [x] **Phase 1: Ingestion & Retrieval Pipeline** - Documents go in, relevant chunks come out
- [x] **Phase 2: Generation, API & Observability** - Questions go in, cited answers come out via REST API
- [x] **Phase 3: Evaluation & CI/CD Quality Gates** - Automated measurement proves the system works
- [ ] **Phase 4: Frontend & Portfolio** - Users interact visually, hiring managers see proof

## Phase Details

### Phase 1: Ingestion & Retrieval Pipeline
**Goal**: Users can upload documents in any supported format and retrieve relevant chunks via hybrid search
**Depends on**: Nothing (first phase)
**Requirements**: ING-01, ING-02, ING-03, ING-04, ING-05, ING-06, ING-07, ING-08, ING-09, ING-10, RET-01, RET-02, RET-03, RET-04, RET-05
**Success Criteria** (what must be TRUE):
  1. User can upload a PDF, Markdown, TXT, or HTML file and see it appear in the document list
  2. Uploaded documents are chunked with correct metadata (source, page, position) visible in the index
  3. A keyword query (e.g., exact phrase from a document) returns relevant chunks via hybrid search (BM25 + dense + RRF fusion)
  4. User can delete a document and confirm its chunks are removed from both indexes
  5. Retrieval returns top-5 ranked chunks after fusion, with configurable top-k and threshold parameters
**Plans:** 3 plans

Plans:
- [x] 01-01-PLAN.md — Project foundation, core modules, and document text extractors (PDF/MD/TXT/HTML)
- [x] 01-02-PLAN.md — Chunking engine, dual storage adapters (ChromaDB + BM25), and ingestion pipeline
- [x] 01-03-PLAN.md — Hybrid retrieval (dense + sparse + RRF fusion) and document management

### Phase 2: Generation, API & Observability
**Goal**: Users can ask questions via REST API and receive grounded, citation-enforced answers with full pipeline tracing
**Depends on**: Phase 1 (requires indexed documents and working retrieval)
**Requirements**: GEN-01, GEN-02, GEN-03, GEN-04, GEN-05, GEN-06, API-01, API-02, API-03, API-04, API-05, API-06, OBS-01, OBS-02, OBS-03
**Success Criteria** (what must be TRUE):
  1. POST /query with a question returns structured JSON with answer, citations (chunk text, doc name, page, score), and confidence score
  2. System refuses to answer (returns refusal with reason) when retrieved evidence is insufficient or confidence is below threshold
  3. All API endpoints (query, upload, list, delete, health) work via Swagger UI with proper error handling
  4. Each query is traced end-to-end (retrieval latency, LLM tokens, chunk scores) visible in Arize Phoenix dashboard
  5. Gemini Flash is used as primary LLM with automatic fallback to Qwen when unavailable
**Plans:** 2 plans

Plans:
- [x] 02-01-PLAN.md — Generation response models, LLM factory (Gemini + Qwen fallback), grounding prompts, and RAG chain with refusal logic
- [x] 02-02-PLAN.md — FastAPI REST API (query, upload, list, delete, health), latency middleware, and Phoenix observability tracing

### Phase 3: Evaluation & CI/CD Quality Gates
**Goal**: The system's quality is automatically measured and regressions are blocked before they merge
**Depends on**: Phase 2 (requires full query pipeline for end-to-end evaluation)
**Requirements**: EVAL-01, EVAL-02, EVAL-03, EVAL-04, EVAL-05, EVAL-06, EVAL-07, EVAL-08, EVAL-09, CI-01, CI-02, CI-03, CI-04
**Success Criteria** (what must be TRUE):
  1. Golden dataset of 50+ Q&A pairs exists and evaluation pipeline runs all metrics against it (Faithfulness, Answer Relevancy, Context Recall, Context Precision, Refusal Accuracy, Citation Accuracy, Hallucination rate)
  2. All metric targets are met: Faithfulness >0.85, Answer Relevancy >0.80, Context Recall >0.75, Context Precision >0.70, Refusal Accuracy >90%, Citation Accuracy >95%, Hallucination <5%
  3. GitHub Actions runs evaluation on every PR and blocks merge when any metric drops below threshold
  4. Naive (dense-only) vs hybrid benchmark comparison exists with side-by-side metric results proving hybrid is better
  5. CI pipeline includes linting and type checking alongside evaluation
**Plans:** 4 plans

Plans:
- [x] 03-01-PLAN.md — Test fixture documents (3 topics), golden dataset (50 Q&A pairs), evaluation conftest with session-scoped pipeline fixtures
- [x] 03-02-PLAN.md — 6 evaluation metric modules (faithfulness, relevancy, context recall/precision, refusal accuracy, citation accuracy)
- [x] 03-03-PLAN.md — Quality gate tests (CI-safe + local-only), benchmark tests, CLI evaluation and benchmark scripts, pyproject.toml updates
- [x] 03-04-PLAN.md — GitHub Actions CI/CD (lint, type check, tests, evaluation), PR blocking on metric regression, artifact uploads

### Phase 4: Frontend & Portfolio
**Goal**: Users interact with RAGReady through a polished UI, and hiring managers can evaluate the project from the README alone
**Depends on**: Phase 2 (API endpoints), Phase 3 (evaluation results for portfolio artifacts)
**Requirements**: UI-01, UI-02, UI-03, UI-04, UI-05, PORT-01, PORT-02, PORT-03, PORT-04, PORT-05
**Success Criteria** (what must be TRUE):
  1. User can type a question in the chat interface and see the answer with source citations panel and confidence indicator
  2. User can upload documents and manage them (list, delete) through the frontend
  3. README includes architecture diagram, CI badge, quick start instructions, and links to evaluation dashboard
  4. Demo video (2 min) walks through the complete workflow: upload → query → cited answer → evaluation results
  5. CI quality gate screenshot shows a blocked PR with metric regression
**Plans:** 3 plans

Plans:
- [ ] 04-01-PLAN.md — Scaffold Vite+React+TS project with shadcn/ui, API client, TypeScript types, and TanStack Query hooks
- [ ] 04-02-PLAN.md — Chat interface (messages, citations, confidence), document management UI (upload, list, delete), app layout with health status
- [ ] 04-03-PLAN.md — Portfolio artifacts (README with architecture diagram and badges, evaluation dashboard, demo video script)

## Progress

**Execution Order:** Phase 1 → Phase 2 → Phase 3 → Phase 4

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Ingestion & Retrieval | 3/3 | Complete | 2026-03-05 |
| 2. Generation, API & Observability | 2/2 | Complete | 2026-03-06 |
| 3. Evaluation & CI/CD Quality Gates | 4/4 | Complete | 2026-03-06 |
| 4. Frontend & Portfolio | 0/2 | Not started | - |
