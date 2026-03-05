# Technology Stack

**Project:** RAGReady — Production-Grade RAG System
**Researched:** 2026-03-04
**Overall Confidence:** HIGH

---

## Recommended Stack

### Core Framework & Runtime

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| Python | 3.12 | Runtime | Latest stable with full library compat. 3.13 has edge-case issues with some ML libs. 3.12 offers performance gains (PEP 684) and is supported by ALL libraries in this stack. | HIGH |
| FastAPI | >=0.135.0 | API server | Industry standard for Python APIs. Built on Pydantic v2 for request/response validation, async-native, auto-generates OpenAPI docs. No real competitor for this use case. | HIGH |
| Pydantic | >=2.12.0 | Data validation | Required by FastAPI. Use for all data models (chunks, citations, query/response schemas). v2 is 5-50x faster than v1. Production/Stable status. | HIGH |
| Uvicorn | latest | ASGI server | Default FastAPI server. Use `uvicorn[standard]` for production (includes uvloop). | HIGH |

### LLM Orchestration

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| LangChain Core | >=1.2.0 | Orchestration primitives | Use LangChain (v1.x+ stable since Oct 2025) for chain composition, prompt templates, and output parsers. The modular `langchain-core` package is stable (Production/Stable status) and avoids the bloat of the monolithic `langchain` package. LangChain v1.x is the correct choice over LlamaIndex because: (1) better Gemini integration via `langchain-google-genai`, (2) more granular control over prompt engineering for citation enforcement, (3) larger community + more debugging resources. | HIGH |
| langchain-google-genai | >=4.2.0 | Gemini LLM integration | Official LangChain integration for Google Gemini. Actively maintained (released Feb 2026). Provides `ChatGoogleGenerativeAI` for Gemini Flash. Free tier access via API key. | HIGH |
| langchain-community | >=0.3.0 | Community integrations | For BM25 retriever, Chroma/Qdrant integrations, and other community-maintained components. | MEDIUM |

**Why NOT LlamaIndex:** LlamaIndex (v0.14.x) is excellent for RAG but adds abstraction layers that reduce control over citation prompt engineering. LangChain's LCEL (LangChain Expression Language) gives more explicit control over the retrieval-generation pipeline, which is critical for citation enforcement. LlamaIndex's `CitationQueryEngine` is a black box — we need to own the citation logic.

### LLM Providers

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| Google Gemini Flash (2.0) | API | Primary LLM | Free tier (60 RPM, 1M tokens/day as of early 2026). Fast inference, strong instruction following for structured output (citations). Best cost/performance ratio at $0 budget. | HIGH |
| Qwen 2.5 (7B) via Ollama | latest | Fallback LLM | Local model for offline dev/testing and API rate-limit fallback. Qwen 2.5 7B is the best open-weight model at this parameter size. Run via Ollama for easy local deployment. | MEDIUM |
| Ollama | latest | Local model server | Simplest way to run local models. Single binary, no Python dependencies, OpenAI-compatible API. | MEDIUM |

### Embeddings & Retrieval

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| sentence-transformers | >=5.2.0 | Embedding framework | Production/Stable status. v5.x (released Jul 2025) adds SparseEncoder support and improved reranker APIs. Provides both embedding and cross-encoder reranking in one package. | HIGH |
| all-MiniLM-L6-v2 | - | Embedding model | 384-dim embeddings, ~80MB model, fast inference on CPU. Good quality/speed tradeoff for a portfolio project. Well-benchmarked, widely used. | HIGH |
| cross-encoder/ms-marco-MiniLM-L-6-v2 | - | Reranker model | Best lightweight cross-encoder reranker. Small enough for CPU inference. Dramatically improves retrieval precision (typically 5-15% MRR improvement). Natively supported by sentence-transformers CrossEncoder. | HIGH |
| rank-bm25 | 0.2.2 | Sparse retrieval (BM25) | Simple, dependency-free BM25 implementation. Last updated Feb 2022 but stable (no bugs to fix — it's a math algorithm). Only 8.6KB. Use BM25Okapi variant. | HIGH |

**Note on rank-bm25:** Despite being "unmaintained," BM25 is a well-defined algorithm. The library is tiny, correct, and has no dependencies. For a more maintained alternative, consider `bm25s` or sentence-transformers' new `SparseEncoder` with SPLADE models, but rank-bm25 is simpler and sufficient.

### Vector Stores

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| ChromaDB | >=1.5.0 | Development vector DB | Chroma v1.x (GA since Apr 2025) is the easiest vector DB to set up. In-memory or persistent mode, zero config. Perfect for dev/testing. Now supports hybrid search natively. | HIGH |
| Qdrant Client | >=1.17.0 | Production vector DB (optional) | Superior to Chroma for production: supports named vectors (for hybrid search), built-in sparse vectors, filtering, and horizontal scaling. Free tier on Qdrant Cloud (1GB). Local mode available via `qdrant-client` without a server. | MEDIUM |

**Why ChromaDB primary, Qdrant optional:** For a 5-week portfolio project, ChromaDB v1.x is sufficient and eliminates infrastructure complexity. Qdrant is the upgrade path if the project grows. Design the retrieval layer with a clean abstraction so swapping is trivial.

### Document Processing

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| PyMuPDF | >=1.27.0 | PDF extraction | Fastest Python PDF library. Extracts text with layout preservation, handles complex PDFs. AGPL license is fine for a portfolio project. No external dependencies (unlike pdfplumber/PyPDF2). | HIGH |
| python-markdown | latest | Markdown parsing | For .md file ingestion. Stdlib-adjacent, lightweight. | HIGH |
| BeautifulSoup4 | latest | HTML parsing | For .html file ingestion. Industry standard, well-tested. | HIGH |
| python-docx | latest | DOCX parsing | For Word document ingestion (optional). | LOW |

### Evaluation & Testing

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| Ragas | >=0.4.0 | RAG evaluation framework | The standard RAG evaluation library. v0.4.x (Dec 2025) provides: Faithfulness, Answer Relevancy, Context Precision/Recall metrics. Works with any LLM as judge. Key for CI/CD quality gates. | HIGH |
| DeepEval | >=3.8.0 | LLM testing framework | Complements Ragas with pytest-native test runner (`deepeval test run`). Provides Hallucination, Answer Relevancy, Faithfulness metrics. Key advantage: integrates directly with pytest for CI/CD. Use for quality gate assertions. | HIGH |
| pytest | >=8.0 | Test framework | Standard Python test framework. DeepEval builds on top of it. | HIGH |
| pytest-asyncio | latest | Async test support | Required for testing FastAPI async endpoints. | HIGH |

**Use BOTH Ragas + DeepEval:** Ragas provides the evaluation metrics and dataset generation. DeepEval provides the pytest integration for CI/CD quality gates. They solve different parts of the problem: Ragas = "measure quality," DeepEval = "fail the build if quality drops."

### Frontend

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| React | >=18.x | Frontend framework | Project constraint. Use Vite for tooling. | HIGH |
| TypeScript | >=5.x | Type safety | Non-negotiable for any modern React project. | HIGH |
| Vite | >=6.x | Build tool | Fast dev server, optimized builds. Standard for React in 2026. | HIGH |
| Tailwind CSS | >=4.x | Styling | Utility-first CSS. Fast to build UI without design system overhead. | MEDIUM |

### Infrastructure & DevOps

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| GitHub Actions | - | CI/CD | Project constraint. Free for public repos. | HIGH |
| Docker | latest | Containerization | Consistent dev/prod environments. Required for Qdrant if used. | MEDIUM |
| pre-commit | latest | Code quality hooks | Run linters, formatters, type checkers before commit. | HIGH |
| Ruff | latest | Linter + formatter | Replaces flake8, isort, black in one tool. 10-100x faster. The standard Python linter in 2026. | HIGH |
| mypy | latest | Type checker | Static type checking for Python. Catches bugs before runtime. | MEDIUM |

### Supporting Libraries

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| python-dotenv | latest | Env var management | Loading API keys, config from .env files |
| tenacity | latest | Retry logic | Retrying failed LLM API calls with exponential backoff |
| tiktoken | latest | Token counting | Estimating token usage for chunk sizing and context window management |
| structlog | latest | Structured logging | Production logging with JSON output for debugging RAG pipelines |
| httpx | latest | HTTP client | FastAPI test client, external API calls |
| numpy | latest | Numerical ops | Embedding similarity calculations, RRF score computation |
| pydantic-settings | latest | Config management | Type-safe configuration from env vars |
| aiofiles | latest | Async file I/O | Non-blocking document reading in FastAPI |

---

## Alternatives Considered

| Category | Recommended | Alternative | Why Not Alternative |
|----------|-------------|-------------|---------------------|
| Orchestration | LangChain Core 1.x | LlamaIndex 0.14.x | Less control over citation prompts; heavier abstraction; CitationQueryEngine is opaque |
| Orchestration | LangChain Core 1.x | Raw API calls | Too much boilerplate for chain composition, output parsing, and retry logic |
| Vector DB (dev) | ChromaDB 1.x | FAISS | No metadata filtering, no persistence out-of-box, harder to debug |
| Vector DB (dev) | ChromaDB 1.x | Weaviate | Over-engineered for dev; requires Docker; hybrid search config is complex |
| Vector DB (prod) | Qdrant | Pinecone | No free self-hosted option; vendor lock-in; costs money at scale |
| Vector DB (prod) | Qdrant | Milvus | Heavier to run; more complex ops; Qdrant's local mode is simpler |
| PDF parsing | PyMuPDF | pdfplumber | Slower, less reliable on complex layouts, more dependencies |
| PDF parsing | PyMuPDF | Unstructured.io | Massive dependency tree (GB+), overkill for known doc types |
| Embeddings | all-MiniLM-L6-v2 | text-embedding-3-small (OpenAI) | Costs money per call; external dependency; can't run offline |
| Embeddings | all-MiniLM-L6-v2 | BGE-small-en-v1.5 | Slightly better quality but larger model; MiniLM is more widely tested |
| BM25 | rank-bm25 | Elasticsearch | Massive infrastructure for a single feature; $0 budget constraint |
| BM25 | rank-bm25 | bm25s | Newer/faster but less battle-tested; rank-bm25 is simpler |
| Evaluation | Ragas + DeepEval | Custom metrics only | Reinventing the wheel; Ragas metrics are research-backed |
| Evaluation | Ragas + DeepEval | TruLens | Heavier, more opinionated, less flexible CI/CD integration |
| Linter | Ruff | flake8 + black + isort | Three tools vs one, 100x slower, more config |
| LLM | Gemini Flash | GPT-4o-mini | No free tier; higher cost; Gemini Flash free tier is 60 RPM |
| LLM | Gemini Flash | Claude Haiku | No free tier for API access |
| Local LLM | Qwen 2.5 7B | Llama 3.x 8B | Qwen 2.5 has better instruction following at 7B; both are viable |

---

## What NOT to Use

### Do NOT use LlamaIndex as primary orchestrator
**Why:** For citation-enforced generation, you need explicit control over the prompt that instructs the LLM to cite sources. LlamaIndex's `CitationQueryEngine` and `ResponseSynthesizer` abstract this away. When citation quality is your core value prop, you cannot afford a black-box generation step. LangChain's LCEL lets you build the exact prompt chain you need.

### Do NOT use Unstructured.io for document parsing
**Why:** Pulls in ~2GB of dependencies including detectron2, paddlepaddle, etc. For PDF/MD/TXT/HTML, PyMuPDF + BeautifulSoup + python-markdown covers everything with <50MB of dependencies. Only consider Unstructured if you need OCR on scanned PDFs.

### Do NOT use FAISS as your vector store
**Why:** FAISS is a similarity search library, not a vector database. No metadata filtering, no persistence API, no hybrid search. ChromaDB wraps FAISS-like functionality with a proper database interface.

### Do NOT use Elasticsearch/OpenSearch for BM25
**Why:** Running a JVM-based search engine for BM25 keyword matching is absurd at this scale. `rank-bm25` does the same thing in <10 lines of Python with zero infrastructure.

### Do NOT use OpenAI embeddings
**Why:** Costs money per API call, adds external dependency, can't run offline for testing. `all-MiniLM-L6-v2` runs locally, is free, and is fast enough for this use case. The quality difference is negligible for a domain-specific corpus with a reranker.

### Do NOT use LangSmith/LangFuse for tracing (initially)
**Why:** Observability is important but not in the first 3 phases. Add structured logging with `structlog` first. LangSmith can be added in phase 4-5 if needed. Avoid premature tooling complexity.

### Do NOT use `langchain` (monolithic package)
**Why:** The monolithic `langchain` package bundles everything. Use `langchain-core` + specific integration packages (`langchain-google-genai`, `langchain-community`). This keeps dependencies minimal and imports fast.

### Do NOT use Gradio/Streamlit for the frontend
**Why:** Project specifies React frontend. Gradio/Streamlit are great for prototyping but are not production frontend frameworks. They can't handle custom citation UI, streaming responses properly, or be deployed as a standalone SPA.

---

## Stack Patterns by Phase

### Phase 1: Document Ingestion Layer
```
PyMuPDF + BeautifulSoup4 + python-markdown → Chunking logic → Pydantic models → ChromaDB
sentence-transformers (all-MiniLM-L6-v2) for embedding
```

### Phase 2: Hybrid Retrieval
```
ChromaDB (dense) + rank-bm25 (sparse) → RRF fusion → cross-encoder reranking
LangChain retrievers for abstraction
```

### Phase 3: Citation-Enforced Generation
```
LangChain Core (LCEL chains) + langchain-google-genai (Gemini Flash)
Pydantic output parser for structured citation responses
Custom citation validation logic
```

### Phase 4: Evaluation Pipeline
```
Ragas (offline evaluation metrics) + DeepEval (pytest-native assertions)
Custom golden dataset
```

### Phase 5: CI/CD Quality Gates
```
GitHub Actions + DeepEval test runner
Ruff + mypy + pytest for code quality
Threshold-based quality gates on Ragas metrics
```

---

## Version Compatibility Matrix

| Library | Min Python | Notes |
|---------|-----------|-------|
| langchain-core 1.2.x | 3.10+ | v1.x dropped Python 3.9 |
| langchain-google-genai 4.x | 3.10+ | Follows langchain-core |
| FastAPI 0.135.x | 3.10+ | Dropped 3.9 in 0.112+ |
| Pydantic 2.12.x | 3.9+ | Still supports 3.9 |
| ChromaDB 1.5.x | 3.9+ | Broad support |
| qdrant-client 1.17.x | 3.10+ | Dropped 3.9 in 1.15+ |
| sentence-transformers 5.2.x | 3.10+ | v5.x dropped 3.9 |
| Ragas 0.4.x | 3.9+ | Broad support |
| DeepEval 3.8.x | 3.9+ | Broad support |
| PyMuPDF 1.27.x | 3.10+ | Dropped 3.9 in 1.25+ |
| rank-bm25 0.2.2 | any | No restrictions |

**Conclusion:** Use Python 3.12. All libraries support it. Python 3.10 is the minimum floor across the stack.

---

## Installation

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate  # Windows

# Core API
pip install "fastapi[standard]" pydantic pydantic-settings uvicorn[standard]

# LLM Orchestration
pip install langchain-core langchain-google-genai langchain-community

# Embeddings & Retrieval
pip install sentence-transformers rank-bm25

# Vector Store
pip install chromadb
# pip install qdrant-client  # Optional: for production

# Document Processing
pip install PyMuPDF beautifulsoup4 markdown python-docx

# Evaluation
pip install ragas deepeval

# Supporting
pip install python-dotenv tenacity tiktoken structlog httpx numpy aiofiles

# Dev dependencies
pip install pytest pytest-asyncio pytest-cov ruff mypy pre-commit httpx
```

### Alternative: requirements files
```bash
# requirements.txt (production)
fastapi[standard]>=0.135.0
pydantic>=2.12.0
pydantic-settings>=2.0.0
uvicorn[standard]>=0.30.0
langchain-core>=1.2.0
langchain-google-genai>=4.2.0
langchain-community>=0.3.0
sentence-transformers>=5.2.0
rank-bm25>=0.2.2
chromadb>=1.5.0
PyMuPDF>=1.27.0
beautifulsoup4>=4.12.0
markdown>=3.5
ragas>=0.4.0
deepeval>=3.8.0
python-dotenv>=1.0.0
tenacity>=8.0.0
tiktoken>=0.7.0
structlog>=24.0.0
httpx>=0.27.0
numpy>=1.26.0
aiofiles>=24.0.0

# requirements-dev.txt
pytest>=8.0.0
pytest-asyncio>=0.24.0
pytest-cov>=5.0.0
ruff>=0.9.0
mypy>=1.15.0
pre-commit>=4.0.0
```

---

## Sources

All version data verified directly from PyPI on 2026-03-04:

| Library | PyPI Version | Release Date | Confidence |
|---------|-------------|--------------|------------|
| langchain-core | 1.2.17 | Mar 2, 2026 | HIGH — verified PyPI |
| langchain-google-genai | 4.2.1 | Feb 19, 2026 | HIGH — verified PyPI |
| llama-index-core | 0.14.15 | Feb 18, 2026 | HIGH — verified PyPI |
| FastAPI | 0.135.1 | Mar 1, 2026 | HIGH — verified PyPI |
| Pydantic | 2.12.5 | Nov 26, 2025 | HIGH — verified PyPI |
| ChromaDB | 1.5.2 | Feb 27, 2026 | HIGH — verified PyPI |
| qdrant-client | 1.17.0 | Feb 19, 2026 | HIGH — verified PyPI |
| sentence-transformers | 5.2.3 | Feb 17, 2026 | HIGH — verified PyPI |
| Ragas | 0.4.3 | Jan 13, 2026 | HIGH — verified PyPI |
| DeepEval | 3.8.8 | Feb 26, 2026 | HIGH — verified PyPI |
| PyMuPDF | 1.27.1 | Feb 11, 2026 | HIGH — verified PyPI |
| rank-bm25 | 0.2.2 | Feb 16, 2022 | HIGH — verified PyPI (stable, no updates needed) |

### Key observations from version research:
1. **LangChain v1.x is now stable** — v1.0.0 released Oct 17, 2025. The 0.3.x line is still receiving patches (0.3.83, Jan 2026) for backward compat but new projects should use 1.x.
2. **sentence-transformers v5.x is a major upgrade** — Added SparseEncoder for SPLADE models, improved CrossEncoder API. Released Jul 2025.
3. **ChromaDB hit v1.0 in Apr 2025** — Major milestone. Now production-ready with stable API.
4. **Ragas jumped to 0.4.x** — Breaking changes from 0.2.x. New `llm_factory` API, `AspectCritic` for custom metrics. Check migration guide if using older tutorials.
5. **DeepEval v3.x** — Major version with DAG metrics, component-level evaluation via `@observe`. Actively maintained (multiple releases per month).
