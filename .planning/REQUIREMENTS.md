# Requirements: RAGReady

**Defined:** 2026-03-04
**Core Value:** Every generated answer must be grounded in retrieved evidence with verifiable citations — the system refuses to answer rather than hallucinate.

## v1 Requirements

Requirements for initial release. Each maps to roadmap phases.

### Ingestion

- [ ] **ING-01**: User can upload PDF documents and have text extracted for indexing
- [ ] **ING-02**: User can upload Markdown files and have content parsed for indexing
- [ ] **ING-03**: User can upload plain text files for indexing
- [ ] **ING-04**: User can upload HTML files and have content extracted (tags stripped) for indexing
- [ ] **ING-05**: Uploaded documents are chunked using recursive/semantic strategy with configurable chunk size (default 512 tokens) and overlap (default 50 tokens)
- [ ] **ING-06**: Each chunk stores metadata including source document name, page number, and position within document
- [ ] **ING-07**: Chunks are embedded using all-MiniLM-L6-v2 and stored in ChromaDB vector index
- [ ] **ING-08**: Chunks are indexed in a BM25 sparse index alongside the dense vector index
- [ ] **ING-09**: User can view a list of all ingested documents with status
- [ ] **ING-10**: User can delete a document and have its chunks removed from both indexes

### Retrieval

- [ ] **RET-01**: System performs dense retrieval via embedding similarity search against ChromaDB
- [ ] **RET-02**: System performs sparse retrieval via BM25 keyword matching
- [ ] **RET-03**: Dense and sparse results are fused using Reciprocal Rank Fusion (RRF) with k=60
- [ ] **RET-04**: User can configure retrieval parameters (top-k, similarity threshold) without code changes
- [ ] **RET-05**: Hybrid retrieval returns top-5 most relevant chunks after fusion

### Generation

- [ ] **GEN-01**: System generates answers using Gemini Flash as primary LLM with local Qwen as fallback
- [ ] **GEN-02**: Generated responses are structured JSON containing answer text, citations array, and confidence score
- [ ] **GEN-03**: Each citation in the response includes the source chunk text, document name, page/section reference, and relevance score
- [ ] **GEN-04**: System refuses to answer (returns refusal with reason) when confidence is below a configurable threshold
- [ ] **GEN-05**: Generation uses temperature 0.0-0.3 to minimize hallucination
- [ ] **GEN-06**: User can see which source documents and chunks were used to generate each answer

### API

- [ ] **API-01**: FastAPI backend exposes a POST /query endpoint that accepts a question and returns structured JSON response
- [ ] **API-02**: FastAPI backend exposes POST /documents/upload endpoint for document ingestion
- [ ] **API-03**: FastAPI backend exposes GET /documents endpoint listing all ingested documents
- [ ] **API-04**: FastAPI backend exposes DELETE /documents/{id} endpoint to remove a document
- [ ] **API-05**: FastAPI backend exposes GET /health endpoint returning system status
- [ ] **API-06**: All API endpoints include proper error handling and OpenAPI documentation

### Frontend

- [ ] **UI-01**: React frontend provides a chat interface where user can type questions and see answers
- [ ] **UI-02**: React frontend displays source citations panel alongside each answer showing document name, page, and relevant chunk text
- [ ] **UI-03**: React frontend shows confidence indicator for each answer (visual representation of confidence score)
- [ ] **UI-04**: React frontend provides document upload interface
- [ ] **UI-05**: React frontend provides document management view (list, delete)

### Evaluation

- [ ] **EVAL-01**: Golden dataset of 50+ question-answer pairs exists covering the ingested document domain
- [ ] **EVAL-02**: Evaluation pipeline measures Faithfulness using Ragas/DeepEval (target >0.85)
- [ ] **EVAL-03**: Evaluation pipeline measures Answer Relevancy (target >0.80)
- [ ] **EVAL-04**: Evaluation pipeline measures Context Recall (target >0.75)
- [ ] **EVAL-05**: Evaluation pipeline measures Context Precision (target >0.70)
- [ ] **EVAL-06**: Evaluation pipeline measures custom Refusal Accuracy metric (target >90%)
- [ ] **EVAL-07**: Evaluation pipeline measures custom Citation Accuracy metric (target >95%)
- [ ] **EVAL-08**: Naive (dense-only, no reranking) vs hybrid pipeline benchmark comparison exists with side-by-side metric results
- [ ] **EVAL-09**: Hallucination rate is measured and tracked (target <5%)

### CI/CD

- [ ] **CI-01**: GitHub Actions workflow runs evaluation suite on every pull request
- [ ] **CI-02**: PRs are blocked when any evaluation metric drops below defined thresholds
- [ ] **CI-03**: Evaluation reports are saved as GitHub Actions artifacts on each run
- [ ] **CI-04**: CI pipeline includes linting and type checking

### Observability

- [ ] **OBS-01**: Arize Phoenix (or equivalent) traces the full RAG pipeline per query: retrieval latency, LLM token usage, chunk relevance scores
- [ ] **OBS-02**: System logs retrieval and generation latency for each query
- [ ] **OBS-03**: Observability dashboard shows query performance trends

### Portfolio

- [ ] **PORT-01**: Architecture diagram (Mermaid or draw.io) showing all 5 layers and data flow
- [ ] **PORT-02**: README includes CI badge, quick start, and architecture overview
- [ ] **PORT-03**: Evaluation dashboard showing metric trends (HTML page or Streamlit)
- [ ] **PORT-04**: 2-minute demo video walkthrough (Loom or equivalent)
- [ ] **PORT-05**: Screenshot of CI quality gate blocking a PR with regression

## v2 Requirements

Deferred to future release. Tracked but not in current roadmap.

### Retrieval Enhancements

- **RET-V2-01**: Cross-encoder reranking using ms-marco-MiniLM-L-6-v2 after RRF fusion (retrieve top-20, rerank to top-5)
- **RET-V2-02**: Query preprocessing via HyDE or multi-query expansion to improve retrieval on ambiguous queries
- **RET-V2-03**: Metadata enrichment with section header hierarchy and structural context per chunk

### UX Enhancements

- **UX-V2-01**: Real-time streaming responses via FastAPI StreamingResponse
- **UX-V2-02**: Conversation memory / multi-turn chat with history context
- **UX-V2-03**: Additional file format support (DOCX, CSV)

### Advanced Evaluation

- **EVAL-V2-01**: Prompt versioning and A/B testing framework
- **EVAL-V2-02**: Automated golden dataset generation from documents

## Out of Scope

Explicitly excluded. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| Multi-tenant authentication / RBAC | Adds massive auth complexity with zero ML/AI learning value. PrivateGPT doesn't support it either. |
| GraphRAG / Knowledge Graph | Entirely different architecture (entity extraction, graph DB). Even Verba marks it out of scope. |
| Fine-tuned embedding models | Requires labeled data + GPU training — a separate ML project. Pretrained models are excellent for this use case. |
| Multi-language support | Adds testing complexity across languages. English-only for v1. |
| Agentic RAG / Multi-step reasoning | Adds autonomous decision-making complexity orthogonal to demonstrating retrieval quality. |
| Custom UI design system | Over-investing in frontend steals time from ML differentiation. Use component library (shadcn/ui, MUI). |
| Production-scale infrastructure (k8s) | Overengineering for portfolio. Docker Compose is sufficient. |
| Multi-modal ingestion (images, audio) | Requires OCR, speech-to-text — each a complex pipeline. Text-based only. |
| Mobile app | Web-first portfolio project. |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| ING-01 | Phase 1 | Pending |
| ING-02 | Phase 1 | Pending |
| ING-03 | Phase 1 | Pending |
| ING-04 | Phase 1 | Pending |
| ING-05 | Phase 1 | Pending |
| ING-06 | Phase 1 | Pending |
| ING-07 | Phase 1 | Pending |
| ING-08 | Phase 1 | Pending |
| ING-09 | Phase 1 | Pending |
| ING-10 | Phase 1 | Pending |
| RET-01 | Phase 1 | Pending |
| RET-02 | Phase 1 | Pending |
| RET-03 | Phase 1 | Pending |
| RET-04 | Phase 1 | Pending |
| RET-05 | Phase 1 | Pending |
| GEN-01 | Phase 2 | Pending |
| GEN-02 | Phase 2 | Pending |
| GEN-03 | Phase 2 | Pending |
| GEN-04 | Phase 2 | Pending |
| GEN-05 | Phase 2 | Pending |
| GEN-06 | Phase 2 | Pending |
| API-01 | Phase 2 | Pending |
| API-02 | Phase 2 | Pending |
| API-03 | Phase 2 | Pending |
| API-04 | Phase 2 | Pending |
| API-05 | Phase 2 | Pending |
| API-06 | Phase 2 | Pending |
| UI-01 | Phase 4 | Pending |
| UI-02 | Phase 4 | Pending |
| UI-03 | Phase 4 | Pending |
| UI-04 | Phase 4 | Pending |
| UI-05 | Phase 4 | Pending |
| EVAL-01 | Phase 3 | Pending |
| EVAL-02 | Phase 3 | Pending |
| EVAL-03 | Phase 3 | Pending |
| EVAL-04 | Phase 3 | Pending |
| EVAL-05 | Phase 3 | Pending |
| EVAL-06 | Phase 3 | Pending |
| EVAL-07 | Phase 3 | Pending |
| EVAL-08 | Phase 3 | Pending |
| EVAL-09 | Phase 3 | Pending |
| CI-01 | Phase 3 | Pending |
| CI-02 | Phase 3 | Pending |
| CI-03 | Phase 3 | Pending |
| CI-04 | Phase 3 | Pending |
| OBS-01 | Phase 2 | Pending |
| OBS-02 | Phase 2 | Pending |
| OBS-03 | Phase 2 | Pending |
| PORT-01 | Phase 4 | Pending |
| PORT-02 | Phase 4 | Pending |
| PORT-03 | Phase 4 | Pending |
| PORT-04 | Phase 4 | Pending |
| PORT-05 | Phase 4 | Pending |

**Coverage:**
- v1 requirements: 53 total
- Mapped to phases: 53
- Unmapped: 0 ✓

---
*Requirements defined: 2026-03-04*
*Last updated: 2026-03-04 after roadmap creation*
