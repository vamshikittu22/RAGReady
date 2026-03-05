# Architecture Patterns

**Domain:** Production RAG System (Retrieval-Augmented Generation)
**Researched:** 2026-03-04
**Confidence:** HIGH (based on LangChain docs, LlamaIndex docs, Ragas docs, FastAPI docs, ChromaDB docs)

## System Overview

RAGReady has two distinct data flows: an **ingestion pipeline** (offline/batch) and a **query pipeline** (online/real-time). These share storage but operate independently. This separation is a core architectural principle endorsed by both LangChain and LlamaIndex documentation.

```
                         RAGReady System Architecture

 ====================== INGESTION FLOW (Offline) =======================

   [Documents]     [Document Processor]      [Index Builder]
   PDF/MD/TXT/HTML --> Extract + Clean ------> Chunk (512 tok) --+
                        |                        |               |
                        v                        v               |
                   [Metadata Store]        [Chunk Store]         |
                   (source, page,          (raw text +           |
                    hash, timestamp)        metadata)            |
                                                                 |
                        +----------------------------------------+
                        |                        |
                        v                        v
                  [ChromaDB]              [BM25 Index]
                  (dense vectors via      (sparse term
                   MiniLM-L6-v2)          frequency index)
                        |                        |
                        +--- [DVC Versioning] ---+

 ======================= QUERY FLOW (Online) ===========================

   [User Query]
       |
       v
   [FastAPI Gateway]  <-- /api/v1/query
       |
       +---> [Query Preprocessor]
       |         |
       |         v
       |    [Hybrid Retriever]
       |         |                    |
       |         v                    v
       |    [Dense Search]      [BM25 Search]
       |    (ChromaDB)          (sparse index)
       |         |                    |
       |         +----> [RRF Fusion (k=60)] <----+
       |                      |
       |                      v
       |              [Cross-Encoder Reranker]
       |              (ms-marco-MiniLM-L-6-v2)
       |                      |
       |                      v
       |              [Top-5 Chunks + Scores]
       |                      |
       v                      v
   [Citation-Enforced Generator]
       |
       |  Prompt: system + chunks + query
       |  LLM: Gemini Flash (primary) / Qwen (fallback)
       |  Temperature: 0.0-0.3
       |
       v
   [Structured Response]
   {
     "answer": "...",
     "citations": [
       {"chunk_id": "...", "text": "...", "source": "...", "page": N}
     ],
     "confidence": 0.87,
     "model": "gemini-flash"
   }
       |
       v
   [Response Validator]  -- confidence < threshold --> [Refusal Response]
       |
       v
   [Observability Logger]  --> [Arize Phoenix / LangSmith]
       |
       v
   [React Frontend]
   (Chat + Source Panel + Confidence Indicators)

 =================== EVALUATION FLOW (CI/CD) ===========================

   [Golden Dataset (50+ Q&A)]
       |
       v
   [Evaluation Runner]
   (Ragas + DeepEval)
       |
       +---> Faithfulness      (target >0.85)
       +---> Answer Relevancy  (target >0.80)
       +---> Context Recall    (target >0.75)
       +---> Context Precision (target >0.70)
       +---> Refusal Accuracy  (target >0.90)
       +---> Citation Accuracy (target >0.95)
       |
       v
   [GitHub Actions Gate]
   Pass? --> Merge allowed
   Fail? --> PR blocked + report artifact
```

## Component Boundaries

| Component | Responsibility | Communicates With | Interface |
|-----------|---------------|-------------------|-----------|
| **Document Processor** | Extract text from PDF/MD/TXT/HTML, clean, normalize | Index Builder | Internal Python API (function calls) |
| **Chunker** | Split documents into semantic chunks (512 tokens, 50 overlap) with metadata | Dense Indexer, Sparse Indexer | Internal Python API |
| **Dense Indexer** | Embed chunks via sentence-transformers, store in ChromaDB | ChromaDB, Hybrid Retriever | ChromaDB Python client |
| **Sparse Indexer** | Build BM25 index from chunk tokens | BM25 store, Hybrid Retriever | rank_bm25 / custom BM25 class |
| **Hybrid Retriever** | Query both indexes, fuse with RRF, rerank with cross-encoder | Dense Indexer, Sparse Indexer, Cross-Encoder | Internal Python API returning ranked chunks |
| **Citation Generator** | Build structured prompt, call LLM, enforce citation format | LLM API (Gemini/Qwen), Hybrid Retriever | Pydantic response models |
| **Response Validator** | Check confidence threshold, validate citation references | Citation Generator | Pass-through filter |
| **FastAPI Gateway** | HTTP API: query endpoint, upload endpoint, health check | All backend services | REST API (OpenAPI) |
| **React Frontend** | Chat UI, source panel, confidence display | FastAPI Gateway | HTTP/REST |
| **Evaluation Pipeline** | Run Ragas/DeepEval metrics against golden dataset | All pipeline components | CLI / pytest |
| **CI/CD Gates** | Block PRs on metric regression | Evaluation Pipeline, GitHub Actions | GitHub Actions YAML |
| **Observability** | Trace requests, log latency/tokens/costs | All pipeline components | OpenTelemetry / Phoenix SDK |

### Key Boundary Rules

1. **Ingestion and Retrieval are independent services** -- ingestion writes to indexes, retrieval reads from them. They share storage but have no runtime coupling.
2. **Retrieval and Generation are separated** -- the retriever returns ranked chunks with scores; the generator receives chunks as input. This allows measuring retrieval quality independently (a core senior dev principle from PROJECT.md).
3. **The evaluation pipeline operates externally** -- it calls the same API endpoints a user would, or directly invokes pipeline functions. It never modifies pipeline behavior.
4. **The API gateway is thin** -- it handles HTTP concerns (validation, serialization, CORS) and delegates to service layers. No business logic in route handlers.

## Recommended Project Structure

Python monorepo with clear separation of concerns. Based on FastAPI's `APIRouter` pattern for the API layer, with domain-driven service modules.

```
RAGReady/
|
|-- src/
|   |-- ragready/                    # Main Python package
|   |   |-- __init__.py
|   |   |
|   |   |-- api/                     # FastAPI layer (thin)
|   |   |   |-- __init__.py
|   |   |   |-- main.py              # FastAPI app, lifespan, CORS, middleware
|   |   |   |-- dependencies.py      # Shared DI: get_retriever(), get_generator()
|   |   |   |-- routers/
|   |   |   |   |-- __init__.py
|   |   |   |   |-- query.py         # POST /api/v1/query
|   |   |   |   |-- documents.py     # POST /api/v1/documents/upload
|   |   |   |   |-- health.py        # GET /api/v1/health
|   |   |   |   |-- eval.py          # GET /api/v1/eval/status (optional)
|   |   |   |-- schemas/
|   |   |   |   |-- __init__.py
|   |   |   |   |-- query.py         # QueryRequest, QueryResponse, Citation
|   |   |   |   |-- documents.py     # UploadResponse, DocumentStatus
|   |   |   |   |-- health.py        # HealthResponse
|   |   |
|   |   |-- ingestion/               # Document processing pipeline
|   |   |   |-- __init__.py
|   |   |   |-- extractors/
|   |   |   |   |-- __init__.py
|   |   |   |   |-- base.py          # Abstract extractor interface
|   |   |   |   |-- pdf.py           # PDF text extraction
|   |   |   |   |-- markdown.py      # Markdown processing
|   |   |   |   |-- html.py          # HTML text extraction
|   |   |   |   |-- plaintext.py     # Plain text handling
|   |   |   |-- chunker.py           # Semantic chunking (RecursiveCharacterTextSplitter)
|   |   |   |-- pipeline.py          # Orchestrates: extract -> chunk -> index
|   |   |   |-- metadata.py          # Document metadata tracking (hash, source, timestamp)
|   |   |
|   |   |-- retrieval/               # Hybrid retrieval pipeline
|   |   |   |-- __init__.py
|   |   |   |-- dense.py             # ChromaDB dense vector search
|   |   |   |-- sparse.py            # BM25 sparse search
|   |   |   |-- fusion.py            # RRF fusion algorithm
|   |   |   |-- reranker.py          # Cross-encoder reranking
|   |   |   |-- hybrid.py            # Orchestrates: dense + sparse -> fuse -> rerank
|   |   |
|   |   |-- generation/              # Citation-enforced generation
|   |   |   |-- __init__.py
|   |   |   |-- prompts.py           # System prompt templates, citation format instructions
|   |   |   |-- generator.py         # LLM calling, structured output parsing
|   |   |   |-- validator.py         # Confidence threshold, citation cross-reference check
|   |   |   |-- models.py            # LLM provider abstraction (Gemini, Qwen)
|   |   |
|   |   |-- core/                    # Shared infrastructure
|   |   |   |-- __init__.py
|   |   |   |-- config.py            # Pydantic Settings (env vars, model names, thresholds)
|   |   |   |-- models.py            # Shared domain models (Chunk, Document, Citation)
|   |   |   |-- exceptions.py        # Custom exceptions
|   |   |   |-- logging.py           # Structured logging setup
|   |   |   |-- observability.py     # Phoenix/OpenTelemetry tracing setup
|   |   |
|   |   |-- storage/                 # Storage adapters
|   |   |   |-- __init__.py
|   |   |   |-- chroma.py            # ChromaDB client wrapper
|   |   |   |-- bm25_store.py        # BM25 index persistence
|   |   |   |-- document_store.py    # Raw document/chunk storage
|   |
|   |-- frontend/                    # React application
|       |-- src/
|       |   |-- components/
|       |   |   |-- ChatInterface.tsx
|       |   |   |-- SourcePanel.tsx
|       |   |   |-- ConfidenceIndicator.tsx
|       |   |   |-- DocumentUpload.tsx
|       |   |-- hooks/
|       |   |-- services/
|       |   |   |-- api.ts            # FastAPI client
|       |   |-- App.tsx
|       |-- package.json
|       |-- vite.config.ts
|
|-- tests/
|   |-- unit/
|   |   |-- test_chunker.py
|   |   |-- test_fusion.py
|   |   |-- test_reranker.py
|   |   |-- test_generator.py
|   |   |-- test_validator.py
|   |   |-- test_extractors.py
|   |-- integration/
|   |   |-- test_ingestion_pipeline.py
|   |   |-- test_retrieval_pipeline.py
|   |   |-- test_query_endpoint.py
|   |-- evaluation/
|       |-- golden_dataset.json       # 50+ Q&A pairs with ground truth
|       |-- run_eval.py               # Ragas/DeepEval evaluation runner
|       |-- conftest.py               # Evaluation fixtures
|
|-- data/
|   |-- raw/                          # Source documents (gitignored if large)
|   |-- processed/                    # Chunked documents (DVC tracked)
|   |-- indexes/                      # ChromaDB + BM25 index files (DVC tracked)
|
|-- scripts/
|   |-- ingest.py                     # CLI: python scripts/ingest.py --source ./data/raw
|   |-- evaluate.py                   # CLI: python scripts/evaluate.py
|   |-- benchmark.py                  # CLI: naive vs hybrid comparison
|
|-- .github/
|   |-- workflows/
|       |-- ci.yml                    # Lint + unit tests
|       |-- eval.yml                  # Evaluation quality gates
|
|-- pyproject.toml                    # Project config, dependencies (use uv or poetry)
|-- .env.example                      # Required environment variables
|-- .dvc/                             # DVC config for index versioning
|-- .dvcignore
|-- Dockerfile                        # Multi-stage: backend + frontend
|-- docker-compose.yml                # Local dev: backend + frontend + chroma
```

### Structure Rationale

1. **`src/ragready/` layout** (src layout): Prevents accidental imports from the project root during testing. Industry standard for Python packages. ([Source: Python Packaging Guide](https://packaging.python.org/en/latest/discussions/src-layout-vs-flat-layout/))

2. **Four domain packages** (`ingestion/`, `retrieval/`, `generation/`, `core/`): Maps directly to the "4 independent services" principle from PROJECT.md. Each can be developed, tested, and measured independently.

3. **`api/` is separate from domain logic**: FastAPI routers are thin -- they call service functions from `ingestion/`, `retrieval/`, and `generation/`. This follows FastAPI's own `APIRouter` pattern documented in their "Bigger Applications" guide. ([Source: FastAPI docs](https://fastapi.tiangolo.com/tutorial/bigger-applications/))

4. **`schemas/` separate from `models/`**: API schemas (Pydantic models for request/response) live in `api/schemas/`. Domain models (Chunk, Document, Citation) live in `core/models.py`. Prevents coupling between HTTP concerns and business logic.

5. **`storage/` adapters**: Isolates ChromaDB and BM25 behind wrapper classes. When swapping ChromaDB for Qdrant (noted as production option in PROJECT.md), only `storage/chroma.py` changes.

6. **`tests/evaluation/`**: Separate from unit/integration tests because evaluation has different execution characteristics (requires LLM calls, takes minutes, has different pass criteria).

## Architectural Patterns to Follow

### Pattern 1: Pipeline Pattern (Ingestion)

The ingestion flow is a linear pipeline: extract -> chunk -> embed -> index. Each stage transforms data and passes it forward. This is the canonical pattern from both LangChain's `IngestionPipeline` and LlamaIndex's loading documentation.

**What:** Chain of processing stages, each taking input and producing output for the next stage.
**When:** Document ingestion (batch processing).
**Why:** Each stage is independently testable, replaceable, and monitorable.

```python
# src/ragready/ingestion/pipeline.py
from dataclasses import dataclass
from typing import Protocol

class Extractor(Protocol):
    def extract(self, file_path: str) -> str: ...

class Chunker(Protocol):
    def chunk(self, text: str, metadata: dict) -> list[Chunk]: ...

class Indexer(Protocol):
    def index(self, chunks: list[Chunk]) -> None: ...

@dataclass
class IngestionPipeline:
    extractor_registry: dict[str, Extractor]
    chunker: Chunker
    indexers: list[Indexer]  # [DenseIndexer, SparseIndexer]

    def ingest(self, file_path: str, file_type: str) -> IngestionResult:
        extractor = self.extractor_registry[file_type]
        text = extractor.extract(file_path)
        chunks = self.chunker.chunk(text, metadata={"source": file_path})
        for indexer in self.indexers:
            indexer.index(chunks)
        return IngestionResult(chunks_created=len(chunks))
```

### Pattern 2: Strategy Pattern (Retrieval Fusion)

Multiple retrieval strategies (dense, sparse) are combined via a configurable fusion strategy (RRF). This pattern is directly from how LangChain's `EnsembleRetriever` and LlamaIndex's retriever composition work.

**What:** Different retrieval strategies implement a common interface; a fusion component combines their results.
**When:** Hybrid retrieval at query time.

```python
# src/ragready/retrieval/hybrid.py
from typing import Protocol

class Retriever(Protocol):
    def retrieve(self, query: str, k: int) -> list[ScoredChunk]: ...

class FusionStrategy(Protocol):
    def fuse(self, result_lists: list[list[ScoredChunk]]) -> list[ScoredChunk]: ...

class HybridRetriever:
    def __init__(
        self,
        retrievers: list[Retriever],       # [DenseRetriever, SparseRetriever]
        fusion: FusionStrategy,             # RRFFusion(k=60)
        reranker: CrossEncoderReranker,
        top_k: int = 5,
    ):
        self.retrievers = retrievers
        self.fusion = fusion
        self.reranker = reranker
        self.top_k = top_k

    def retrieve(self, query: str) -> list[RankedChunk]:
        # Stage 1: Retrieve from each source
        all_results = [r.retrieve(query, k=20) for r in self.retrievers]
        # Stage 2: Fuse results
        fused = self.fusion.fuse(all_results)
        # Stage 3: Rerank with cross-encoder
        reranked = self.reranker.rerank(query, fused, top_k=self.top_k)
        return reranked
```

### Pattern 3: Structured Output Enforcement (Generation)

The generator enforces structured JSON output with Pydantic model validation. This is the pattern recommended by LangChain's structured output docs and critical for citation-enforced generation.

**What:** LLM output is parsed into a strict Pydantic model; malformed responses trigger retry or refusal.
**When:** Every generation call.

```python
# src/ragready/generation/generator.py
from pydantic import BaseModel, Field

class Citation(BaseModel):
    chunk_id: str
    source_document: str
    page: int | None = None
    text_snippet: str = Field(max_length=200)

class GenerationResponse(BaseModel):
    answer: str
    citations: list[Citation]
    confidence: float = Field(ge=0.0, le=1.0)
    model_used: str

class CitationEnforcedGenerator:
    def __init__(self, llm_provider, confidence_threshold: float = 0.6):
        self.llm = llm_provider
        self.threshold = confidence_threshold

    def generate(self, query: str, chunks: list[RankedChunk]) -> GenerationResponse:
        prompt = self._build_prompt(query, chunks)
        raw_response = self.llm.generate(prompt, response_format=GenerationResponse)

        # Validate citations reference actual chunks
        valid_chunk_ids = {c.chunk_id for c in chunks}
        for citation in raw_response.citations:
            if citation.chunk_id not in valid_chunk_ids:
                raise CitationValidationError(f"Hallucinated citation: {citation.chunk_id}")

        # Refuse if below confidence threshold
        if raw_response.confidence < self.threshold:
            return GenerationResponse(
                answer="I don't have enough information to answer this question confidently.",
                citations=[],
                confidence=raw_response.confidence,
                model_used=raw_response.model_used,
            )

        return raw_response
```

### Pattern 4: Dependency Injection (FastAPI)

Use FastAPI's `Depends()` for service injection. This makes services testable (swap real ChromaDB for mock in tests) and centralizes configuration.

**What:** Services are constructed once at startup and injected into route handlers.
**When:** All API endpoints.

```python
# src/ragready/api/dependencies.py
from functools import lru_cache
from ragready.core.config import Settings
from ragready.retrieval.hybrid import HybridRetriever
from ragready.generation.generator import CitationEnforcedGenerator

@lru_cache
def get_settings() -> Settings:
    return Settings()

def get_retriever(settings: Settings = Depends(get_settings)) -> HybridRetriever:
    # Construct and cache retriever with all sub-components
    ...

def get_generator(settings: Settings = Depends(get_settings)) -> CitationEnforcedGenerator:
    # Construct and cache generator with LLM provider
    ...

# src/ragready/api/routers/query.py
@router.post("/query", response_model=QueryResponse)
async def query(
    request: QueryRequest,
    retriever: HybridRetriever = Depends(get_retriever),
    generator: CitationEnforcedGenerator = Depends(get_generator),
):
    chunks = retriever.retrieve(request.query)
    response = generator.generate(request.query, chunks)
    return response
```

### Pattern 5: Configuration as Pydantic Settings

All tunable parameters (model names, thresholds, chunk sizes, API keys) live in a single `Settings` class loaded from environment variables. This is the pattern FastAPI recommends in its advanced settings docs.

**What:** Single source of truth for all configuration, validated at startup.
**When:** Application initialization.

```python
# src/ragready/core/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Embedding
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    chunk_size: int = 512
    chunk_overlap: int = 50

    # Retrieval
    dense_top_k: int = 20
    sparse_top_k: int = 20
    rrf_k: int = 60
    rerank_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    final_top_k: int = 5

    # Generation
    primary_llm: str = "gemini-flash"
    fallback_llm: str = "qwen"
    temperature: float = 0.1
    confidence_threshold: float = 0.6
    max_tokens: int = 1024

    # Infrastructure
    chroma_host: str = "localhost"
    chroma_port: int = 8000
    chroma_collection: str = "ragready"

    # API keys
    google_api_key: str = ""

    # Observability
    phoenix_endpoint: str = ""
    enable_tracing: bool = True

    model_config = {"env_prefix": "RAGREADY_", "env_file": ".env"}
```

## Data Flow Details

### Ingestion Flow (Offline/Batch)

```
Input Document (PDF/MD/TXT/HTML)
    |
    v
[1. File Type Detection] ---- mime type / extension mapping
    |
    v
[2. Text Extraction]
    |-- PDF: PyMuPDF (fitz) or pdfplumber
    |-- Markdown: markdown-it / raw text
    |-- HTML: BeautifulSoup4 (strip tags, keep structure)
    |-- TXT: direct read with encoding detection
    |
    v
[3. Text Cleaning]
    |-- Normalize whitespace
    |-- Remove headers/footers (PDF)
    |-- Preserve section boundaries
    |
    v
[4. Metadata Extraction]
    |-- Source file path
    |-- Content hash (for dedup/change detection)
    |-- Page numbers (PDF)
    |-- Section headers (MD/HTML)
    |-- Ingestion timestamp
    |
    v
[5. Semantic Chunking]
    |-- RecursiveCharacterTextSplitter
    |-- 512 tokens per chunk, 50 token overlap
    |-- add_start_index=True (track position in source)
    |-- Each chunk gets: chunk_id (UUID), parent_doc_id, metadata
    |
    v
[6. Dual Indexing] (parallel)
    |
    +---> [6a. Dense Indexing]
    |     |-- Embed via all-MiniLM-L6-v2 (384 dims)
    |     |-- Store in ChromaDB collection
    |     |-- Metadata stored alongside vectors
    |
    +---> [6b. Sparse Indexing]
          |-- Tokenize chunks
          |-- Build/update BM25 index
          |-- Persist to disk (pickle or custom format)
    |
    v
[7. Version with DVC]
    |-- Track indexes in data/indexes/
    |-- Commit DVC files to git
```

### Query Flow (Online/Real-Time)

```
User Query (string)
    |
    v
[1. Input Validation] (FastAPI/Pydantic)
    |-- Validate query length
    |-- Sanitize input
    |
    v
[2. Query Preprocessing]
    |-- (Future: query rewriting, expansion)
    |-- Pass-through for v1
    |
    v
[3. Parallel Retrieval]
    |
    +---> [3a. Dense Search]
    |     |-- Embed query with same MiniLM-L6-v2
    |     |-- ChromaDB similarity_search(k=20)
    |     |-- Returns: [(chunk, cosine_score), ...]
    |
    +---> [3b. Sparse Search]
          |-- BM25 query(k=20)
          |-- Returns: [(chunk, bm25_score), ...]
    |
    v
[4. RRF Fusion]
    |-- For each chunk across both result sets:
    |     rrf_score = sum(1 / (k + rank_i)) for each list
    |     where k=60
    |-- Sort by rrf_score descending
    |-- Deduplicate by chunk_id
    |
    v
[5. Cross-Encoder Reranking]
    |-- Take top ~20 fused results
    |-- Score each (query, chunk.text) pair with cross-encoder
    |-- Resort by cross-encoder score
    |-- Return top 5
    |
    v
[6. Prompt Construction]
    |-- System prompt: citation format rules, JSON schema
    |-- Context: top-5 chunks with chunk_ids and source info
    |-- User query
    |
    v
[7. LLM Generation]
    |-- Primary: Gemini Flash (temperature 0.1)
    |-- Fallback: Qwen (if Gemini fails/timeout)
    |-- Parse response into GenerationResponse Pydantic model
    |
    v
[8. Response Validation]
    |-- Verify all citation chunk_ids exist in retrieved chunks
    |-- Check confidence >= threshold
    |-- If below threshold: return refusal response
    |-- If citations invalid: retry once, then refuse
    |
    v
[9. Observability Logging]
    |-- Log trace: query -> retrieval_time -> generation_time
    |-- Log metrics: tokens_used, model, latency, confidence
    |-- Send to Arize Phoenix / LangSmith
    |
    v
[10. HTTP Response]
    |-- Structured JSON (QueryResponse schema)
    |-- Includes: answer, citations[], confidence, model_used
    |-- HTTP 200 (success) or 200 with refusal (below threshold)
```

## Build Order (Dependency-Driven)

The build order is constrained by data dependencies: you can't test retrieval without indexed data, and you can't test generation without retrieved chunks. Each phase produces a testable artifact.

```
Phase 1: Foundation (Week 1)
    |-- core/config.py, core/models.py, core/exceptions.py
    |-- storage/chroma.py (ChromaDB wrapper)
    |-- ingestion/extractors/ (start with plaintext + markdown)
    |-- ingestion/chunker.py
    |-- ingestion/pipeline.py
    |-- scripts/ingest.py (CLI)
    |-- Unit tests for chunker, extractors
    |
    | Deliverable: Can ingest .txt/.md files and see chunks in ChromaDB
    |
    v
Phase 2: Retrieval (Week 2)
    |-- retrieval/dense.py (ChromaDB search)
    |-- retrieval/sparse.py (BM25)
    |-- retrieval/fusion.py (RRF)
    |-- retrieval/reranker.py (cross-encoder)
    |-- retrieval/hybrid.py (orchestrator)
    |-- ingestion/extractors/pdf.py, html.py (complete extractor set)
    |-- storage/bm25_store.py
    |-- Unit tests for fusion, reranker
    |-- Integration test: ingest -> retrieve
    |
    | Deliverable: Can query indexed docs and get ranked chunks
    |
    v
Phase 3: Generation + API (Week 3)
    |-- generation/prompts.py
    |-- generation/models.py (Gemini + Qwen providers)
    |-- generation/generator.py
    |-- generation/validator.py
    |-- api/main.py, api/dependencies.py
    |-- api/routers/query.py, health.py, documents.py
    |-- api/schemas/ (all request/response models)
    |-- Integration test: full query pipeline
    |
    | Deliverable: Working API that returns cited answers
    |
    v
Phase 4: Evaluation + CI (Week 4)
    |-- tests/evaluation/golden_dataset.json
    |-- tests/evaluation/run_eval.py (Ragas + DeepEval)
    |-- scripts/evaluate.py
    |-- scripts/benchmark.py (naive vs hybrid comparison)
    |-- .github/workflows/ci.yml
    |-- .github/workflows/eval.yml
    |-- DVC setup for index versioning
    |
    | Deliverable: Automated quality gates, benchmark results
    |
    v
Phase 5: Frontend + Observability + Polish (Week 5)
    |-- frontend/ (React app)
    |-- core/observability.py (Arize Phoenix integration)
    |-- core/logging.py (structured logging)
    |-- Dockerfile, docker-compose.yml
    |-- Portfolio artifacts (diagram, demo, dashboard)
    |
    | Deliverable: Complete portfolio-ready application
```

### Build Order Rationale

1. **Foundation first** because everything depends on config, models, and storage. ChromaDB wrapper is needed by both ingestion and retrieval.

2. **Ingestion before retrieval** because retrieval needs indexed data to test against. Start with simple extractors (txt/md) and add complex ones (PDF/HTML) in Phase 2.

3. **Retrieval before generation** because the generator takes retrieved chunks as input. Testing generation without real retrieval means testing with mocked data -- useful for unit tests but not for validating the system works end-to-end.

4. **Generation + API together** because the API is thin -- it's mainly wiring. Once generation works as a Python function, wrapping it in FastAPI endpoints is straightforward.

5. **Evaluation in Phase 4** because you need the full pipeline working to evaluate it. Golden dataset creation can start earlier (even in Phase 1), but running Ragas/DeepEval requires the complete query flow.

6. **Frontend last** because it's a consumer of the API. The API can be tested with curl/httpie/Swagger UI during development. The frontend adds portfolio value but doesn't affect core RAG functionality.

## Anti-Patterns to Avoid

### Anti-Pattern 1: Monolithic Pipeline Function
**What:** Putting extract -> chunk -> embed -> search -> generate in one function.
**Why bad:** Impossible to test individual stages, measure individual metrics, or swap components. Violates the "measure retrieval separately from generation" principle.
**Instead:** Pipeline pattern with Protocol/interface-based stages (see Pattern 1 above).

### Anti-Pattern 2: Tight Coupling to ChromaDB
**What:** Importing ChromaDB directly in retrieval/generation code.
**Why bad:** PROJECT.md mentions Qdrant as production option. Direct imports make switching painful.
**Instead:** Storage adapter pattern. `storage/chroma.py` implements a `VectorStore` protocol. Retrieval code depends on the protocol, not the implementation.

### Anti-Pattern 3: Unvalidated LLM Output
**What:** Trusting LLM output format without Pydantic validation. Just parsing JSON with `json.loads()`.
**Why bad:** LLMs produce malformed JSON, hallucinated citations, and inconsistent formats. This is the #1 failure mode in production RAG.
**Instead:** Pydantic model validation with retry logic. If the LLM's response doesn't parse into `GenerationResponse`, retry once with an explicit format reminder, then refuse.

### Anti-Pattern 4: Shared Mutable State Between Requests
**What:** Using module-level mutable variables for retriever/index state.
**Why bad:** Race conditions in async FastAPI, impossible to test in isolation.
**Instead:** FastAPI dependency injection with `@lru_cache` for expensive-to-construct singletons (like the retriever). Immutable after construction.

### Anti-Pattern 5: Evaluation in Production Code
**What:** Putting Ragas/DeepEval calls inside the generation pipeline.
**Why bad:** Evaluation is expensive (multiple LLM calls per metric), adds latency, and confuses concerns. Evaluation is an external observer, not a pipeline component.
**Instead:** Evaluation lives in `tests/evaluation/` and runs in CI. It calls the same functions/endpoints but is never in the request path.

### Anti-Pattern 6: Fat API Routes
**What:** Business logic (retrieval, prompt building, validation) inside FastAPI route handlers.
**Why bad:** Can't test business logic without spinning up HTTP server. Violates separation of concerns.
**Instead:** Route handlers call service functions. Business logic lives in `retrieval/`, `generation/`, `ingestion/` packages.

## Scalability Considerations

| Concern | At 100 docs | At 10K docs | At 100K docs |
|---------|-------------|-------------|--------------|
| **Vector Search** | ChromaDB in-memory, <10ms | ChromaDB persistent, <50ms | Qdrant with HNSW, <100ms |
| **BM25 Index** | In-memory rank_bm25, instant | In-memory but ~100MB RAM | Elasticsearch/Tantivy for disk-backed sparse search |
| **Embedding** | CPU, ~2s/doc batch | CPU batch, ~minutes total | GPU or API embeddings, async batching |
| **Reranking** | CPU cross-encoder, <100ms/query | Same (only reranks top-20) | Same (reranking is per-query, not per-corpus) |
| **Ingestion** | Synchronous, fine | Background tasks (FastAPI `BackgroundTasks`) | Celery/Redis task queue |
| **Storage** | Local disk, git-tracked | DVC + cloud remote (S3/GCS) | Managed vector DB (Qdrant Cloud, Pinecone) |

**For RAGReady v1 (portfolio):** 100-1000 docs is realistic. In-memory ChromaDB with persistent storage and in-memory BM25 are sufficient. The architecture supports scaling (adapter pattern for storage) but doesn't need to implement it for v1.

## Integration Points

| External System | Integration Method | Purpose | When Needed |
|---|---|---|---|
| **ChromaDB** | `chromadb` Python client | Dense vector storage & search | Phase 1 (Day 1) |
| **sentence-transformers** | `sentence_transformers` Python lib | Embedding generation (all-MiniLM-L6-v2) | Phase 1 |
| **rank-bm25** | `rank_bm25` Python lib | BM25 sparse retrieval | Phase 2 |
| **cross-encoder** | `sentence_transformers.CrossEncoder` | Reranking | Phase 2 |
| **Google Gemini** | `google-generativeai` SDK | Primary LLM for generation | Phase 3 |
| **Qwen (local)** | `transformers` or `ollama` | Fallback LLM for offline dev | Phase 3 |
| **Ragas** | `ragas` Python lib | RAG evaluation metrics | Phase 4 |
| **DeepEval** | `deepeval` Python lib | Additional RAG evaluation | Phase 4 |
| **Arize Phoenix** | `arize-phoenix` + OpenTelemetry | Observability & tracing | Phase 5 |
| **DVC** | `dvc` CLI tool | Index versioning | Phase 4 |
| **GitHub Actions** | YAML workflow configs | CI/CD quality gates | Phase 4 |

## Sources

- **LangChain RAG Tutorial**: https://python.langchain.com/docs/tutorials/rag/ -- Canonical RAG architecture (Load -> Split -> Store -> Retrieve -> Generate). Verified 2026-03-04. **HIGH confidence.**
- **LlamaIndex RAG Overview**: https://docs.llamaindex.ai/en/stable/understanding/rag/ -- Indexing and querying patterns, ingestion pipeline concept. Verified 2026-03-04. **HIGH confidence.**
- **FastAPI Bigger Applications**: https://fastapi.tiangolo.com/tutorial/bigger-applications/ -- APIRouter pattern, project structure, dependency injection. Verified 2026-03-04. **HIGH confidence.**
- **ChromaDB Documentation**: https://docs.trychroma.com/docs/overview/introduction -- Dense + sparse + hybrid search capabilities. Verified 2026-03-04. **HIGH confidence.**
- **Ragas Documentation**: https://docs.ragas.io/en/stable/getstarted/ -- RAG evaluation metrics (Faithfulness, Context Precision, etc.). Verified 2026-03-04. **HIGH confidence.**
- **Arize Phoenix Documentation**: https://docs.arize.com/phoenix -- OpenTelemetry-based tracing, RAG analysis, evaluation integration. Verified 2026-03-04. **HIGH confidence.**
- **RRF (Reciprocal Rank Fusion)**: Cormack et al., 2009 -- "Reciprocal Rank Fusion outperforms Condorcet and individual Rank Learning Methods." Well-established algorithm, k=60 is the standard default. **HIGH confidence** (established research).
- **Python src layout**: https://packaging.python.org/en/latest/discussions/src-layout-vs-flat-layout/ -- Recommended project structure. **HIGH confidence.**
