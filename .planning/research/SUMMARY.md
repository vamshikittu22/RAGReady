# Project Research Summary

**Project:** RAGReady
**Domain:** Production RAG System (Retrieval-Augmented Generation)
**Researched:** 2026-03-04
**Confidence:** HIGH

## Executive Summary

RAGReady is a production-grade Retrieval-Augmented Generation system designed as a senior ML engineering portfolio project. The research reveals a well-established domain with clear architectural patterns: experts build RAG systems as two decoupled pipelines (offline ingestion and online query), use hybrid retrieval (dense vectors + BM25 sparse search with RRF fusion), add cross-encoder reranking for precision, and enforce structured output with citation validation. The technology stack is mature — Python 3.12, FastAPI, LangChain Core 1.x, sentence-transformers 5.x, ChromaDB 1.x, and Gemini Flash as the primary LLM — with all libraries at stable/production status and strong compatibility. This is not a novel system architecture; it is a well-documented pattern where execution quality and engineering rigor are the differentiators.

The recommended approach is a 5-phase build following strict data dependency order: ingestion first (because retrieval needs indexed data), retrieval second (because generation needs retrieved chunks), generation + API third (the integration point), evaluation fourth (requires the full pipeline), and frontend + polish last (consumer of everything else). Three features differentiate RAGReady from the hundreds of RAG tutorials and OSS projects: citation-enforced structured output with confidence-based refusal, automated evaluation with CI/CD quality gates that block regressions, and data-driven architecture decisions via naive-vs-hybrid benchmarks. No competitor (Verba, PrivateGPT, LangChain templates) combines all three.

The key risks are concentrated in two areas: LLM output reliability (Gemini Flash will produce malformed JSON and hallucinated citations — Pydantic validation with retry logic is mandatory) and evaluation framework stability (Ragas 0.4.x has breaking API changes from widely-cited tutorials — pin versions and use only official docs). Secondary risks include BM25/ChromaDB index desynchronization during dual indexing, Gemini free tier rate limits impacting CI evaluation runs, and chunking strategies that destroy context. All are well-understood with concrete mitigations documented in research.

## Key Findings

### Recommended Stack

The stack centers on Python 3.12 with all libraries verified at compatible, production-stable versions as of March 2026. LangChain Core 1.x is chosen over LlamaIndex for explicit control over citation prompt engineering — LlamaIndex's `CitationQueryEngine` is a black box that prevents the fine-grained citation logic RAGReady requires. Gemini Flash 2.0 provides free-tier LLM access (60 RPM, 1M tokens/day) with Qwen 2.5 7B via Ollama as local fallback.

**Core technologies:**
- **FastAPI + Pydantic v2**: API server with auto-validation — industry standard, async-native, auto-generates OpenAPI docs
- **LangChain Core 1.x + langchain-google-genai**: LLM orchestration — LCEL gives explicit control over citation prompts; stable v1.x since Oct 2025
- **sentence-transformers 5.x (all-MiniLM-L6-v2 + ms-marco-MiniLM cross-encoder)**: Embeddings + reranking — local, free, CPU-viable, one package for both
- **ChromaDB 1.x**: Vector store — GA since Apr 2025, zero-config, persistent mode, hybrid search support
- **rank-bm25**: Sparse retrieval — tiny (8.6KB), correct, zero dependencies; BM25 is a math algorithm that doesn't need updates
- **Ragas 0.4.x + DeepEval 3.x**: Evaluation — Ragas for metrics, DeepEval for pytest-native CI integration
- **React 18 + Vite + TypeScript + Tailwind**: Frontend — per project constraints
- **Gemini Flash 2.0 (free tier)**: Primary LLM — best cost/performance at $0 budget

**Critical version notes:** Python 3.12 (not 3.13 — ML lib edge cases). Pin Ragas 0.4.3 and DeepEval 3.8.8 exactly. Use `langchain-core` (not monolithic `langchain`). Use `chromadb.PersistentClient` (not ephemeral).

### Expected Features

**Must have (table stakes):**
- Multi-format document ingestion (PDF, MD, TXT, HTML) — every RAG system does this
- Semantic/recursive chunking with configurable strategy and metadata — naive chunking is a tutorial anti-pattern
- Dense vector embedding + retrieval — the literal core of RAG
- LLM-powered answer generation with source attribution — users must know WHERE answers come from
- REST API backend with OpenAPI docs — expected interface pattern
- Chat/query UI with document management (upload, list, delete) — portfolio project needs a UI
- Configurable retrieval parameters (top-k, thresholds) — every serious system exposes these
- Basic evaluation metrics — without measurement, it's a demo not a system

**Should have (differentiators — these are P0):**
- Hybrid retrieval with BM25 + dense + RRF fusion (D1) — production systems use this; tutorials don't
- Cross-encoder reranking (D2) — 5-15% MRR improvement; competitors list as "planned"
- Citation-enforced structured output with confidence-based refusal (D3) — **the killer differentiator**; no competitor does this
- Automated evaluation pipeline with golden dataset (D5) — proves ML engineering maturity
- CI/CD quality gates that block on metric regression (D6) — visible proof of rigor
- Naive vs. hybrid benchmark comparison (D4) — data-driven decision evidence

**Defer (v2+):**
- Multi-tenant auth/RBAC, GraphRAG, agentic RAG, fine-tuned embeddings, multi-language, multi-modal, streaming responses, conversation memory

### Architecture Approach

RAGReady follows a two-pipeline architecture: an offline ingestion pipeline (extract → chunk → dual-index) and an online query pipeline (retrieve → fuse → rerank → generate → validate). These share storage (ChromaDB + BM25 index) but are decoupled at runtime. A third flow — the evaluation pipeline — runs externally in CI, calling the same interfaces without modifying behavior. The project uses a Python src-layout monorepo with four domain packages (`ingestion/`, `retrieval/`, `generation/`, `core/`) plus a thin FastAPI API layer and a React frontend.

**Major components:**
1. **Document Processor + Chunker** — Extract text from PDF/MD/TXT/HTML, clean, semantic chunk (512 tokens, 50 overlap), enrich metadata
2. **Dual Indexer** — Embed chunks via MiniLM and store in ChromaDB (dense); tokenize and build BM25 index (sparse)
3. **Hybrid Retriever** — Query both indexes, RRF fusion (k=60), cross-encoder rerank to top-5
4. **Citation-Enforced Generator** — Build structured prompt with chunks, call Gemini Flash, parse into Pydantic model, validate citations against actual chunks, refuse below confidence threshold
5. **Response Validator** — Cross-reference cited chunk IDs against retrieved chunks, enforce confidence threshold, return refusal if criteria not met
6. **Evaluation Pipeline** — Ragas + DeepEval against golden dataset (50+ Q&A pairs); 6 metrics with threshold targets; GitHub Actions quality gates

**Key patterns:** Pipeline (ingestion), Strategy (retrieval fusion), Structured Output Enforcement (generation), Dependency Injection (FastAPI), Configuration as Pydantic Settings. Anti-patterns to avoid: monolithic pipeline functions, tight coupling to ChromaDB, unvalidated LLM output, fat API routes, evaluation in production code.

### Critical Pitfalls

1. **Trusting LLM output without validation** — Gemini Flash will produce malformed JSON and hallucinated citations. Prevent with Pydantic model parsing, citation ID cross-validation against retrieved chunks, retry logic (1 retry with format reminder), and graceful refusal on failure. Never use raw `json.loads()`.

2. **BM25/ChromaDB index desynchronization** — Dual indexing means two write paths that can diverge on partial failure. Prevent with atomic `ingest()` function that writes to both, `verify_sync()` check at startup, and shared document manifest. Run sync verification after every ingestion batch.

3. **Ragas/DeepEval API breaking changes** — Most tutorials reference Ragas 0.2.x; current is 0.4.x with breaking changes (new `llm_factory`, `AspectCritic`, changed function signatures). Prevent by pinning exact versions, using ONLY official docs, checking migration guide, and smoke-testing eval pipeline early.

4. **Gemini free tier rate limits stalling CI** — Evaluation runs need 600-1000 LLM calls (50 Q&A × 4 metrics × 3-5 calls). At 60 RPM = 15+ min minimum. Prevent with exponential backoff (tenacity), local Qwen for dev eval, result caching, small smoke dataset (5-10 pairs), and only running full eval on PR merges.

5. **Chunking strategy destroying context** — Fixed-size chunking splits sentences, tables, and code blocks mid-thought. Prevent with RecursiveCharacterTextSplitter using paragraph-first separators, 50-token overlap, document-type-specific splitting, and manual inspection of 20-30 random chunks per document type before building downstream components.

## Implications for Roadmap

Based on combined research, the build order is dictated by strict data dependencies. Each phase produces a testable deliverable and depends on the previous phase's output.

### Phase 1: Document Ingestion Foundation
**Rationale:** Everything depends on having indexed documents. Retrieval can't be tested without data. Chunking strategy is the single highest-impact decision and must be validated before proceeding.
**Delivers:** Working ingestion pipeline — extract text, chunk semantically, embed and store in ChromaDB + BM25. CLI to ingest documents. Manually inspected chunk quality.
**Addresses:** T1 (multi-format ingestion), T2 (semantic chunking), T3 (dense embedding), T8 (document management)
**Avoids:** Pitfall 5 (chunking context destruction — manually inspect chunks), Pitfall 10 (over-engineering structure — start simple), Pitfall 14 (git bloat — .gitignore day one)
**Stack:** PyMuPDF, BeautifulSoup4, python-markdown, sentence-transformers (all-MiniLM-L6-v2), ChromaDB, rank-bm25, Pydantic

### Phase 2: Hybrid Retrieval
**Rationale:** Retrieval quality is foundational to generation quality. The hybrid approach (dense + BM25 + reranking) is the core technical differentiator. Must be proven and measured before building generation.
**Delivers:** Complete retrieval pipeline — dense search, BM25 sparse search, RRF fusion (k=60), cross-encoder reranking to top-5. Measurable retrieval metrics.
**Addresses:** D1 (hybrid retrieval + RRF), D2 (cross-encoder reranking), T10 (configurable retrieval parameters)
**Avoids:** Pitfall 2 (index desync — build verify_sync()), Pitfall 6 (reranker latency — benchmark early, pre-load model), Pitfall 8 (embedding model mismatch — store model name in collection metadata)
**Stack:** rank-bm25, cross-encoder/ms-marco-MiniLM-L-6-v2, RRF fusion algorithm

### Phase 3: Citation-Enforced Generation + API
**Rationale:** Generation requires retrieved chunks as input (Phase 2 dependency). The API is thin wiring. Citation enforcement is the killer feature — it must be built WITH the generator, not bolted on later. This is where the product's identity is defined.
**Delivers:** Working API returning structured JSON with verifiable citations and confidence-based refusal. The complete query pipeline end-to-end.
**Addresses:** T4 (LLM generation), D3 (citation-enforced structured output), T5 (source attribution), T6 (REST API)
**Avoids:** Pitfall 1 (trusting LLM output — Pydantic validation + retry), Pitfall 12 (Gemini structured output inconsistency — use `with_structured_output()` + fallback parsing), Pitfall 16 (empty retrieval — handle 0-chunk case before calling generator)
**Stack:** LangChain Core (LCEL chains), langchain-google-genai (Gemini Flash), Ollama + Qwen (fallback), FastAPI, Pydantic output parsers

### Phase 4: Evaluation + CI/CD Quality Gates
**Rationale:** Evaluation requires the full pipeline working end-to-end. Golden dataset creation can start earlier (recommend starting in Phase 1), but running Ragas/DeepEval metrics requires Phase 3 to be complete. This phase produces the portfolio's strongest differentiators after citation enforcement.
**Delivers:** Automated evaluation pipeline with 50+ golden Q&A pairs, Ragas/DeepEval metrics (Faithfulness >0.85, Answer Relevancy >0.80, Context Recall >0.75, Context Precision >0.70), naive-vs-hybrid benchmark comparison, GitHub Actions quality gates that block PRs on metric regression.
**Addresses:** T9 (evaluation metrics), D5 (automated eval pipeline), D4 (naive vs hybrid benchmark), D6 (CI/CD quality gates)
**Avoids:** Pitfall 3 (Ragas/DeepEval breaking changes — pin versions, official docs only), Pitfall 4 (rate limits — local Qwen for dev, cache results, smoke dataset), Pitfall 9 (metrics don't reflect quality — multiple metrics + adversarial queries + manual spot checks), Pitfall 15 (inconsistent chunk IDs — deterministic hashing)
**Stack:** Ragas 0.4.3, DeepEval 3.8.8, pytest, GitHub Actions, DVC

### Phase 5: Frontend + Observability + Portfolio Polish
**Rationale:** Frontend consumes the API (Phase 3 dependency). Observability adds tracing without changing behavior. Portfolio artifacts require the complete system. Time-box strictly to 2-3 days for frontend.
**Delivers:** React chat UI with source panel and confidence indicators. Arize Phoenix tracing. Docker Compose deployment. Architecture diagram, demo video, eval dashboard.
**Addresses:** T7 (chat UI), D7 (observability/tracing), D9 (portfolio artifacts), D8 (metadata enrichment refinement)
**Avoids:** Pitfall 11 (frontend scope creep — 2-3 days max, functional > beautiful, use Tailwind + shadcn/ui)
**Stack:** React 18, TypeScript, Vite, Tailwind CSS, Arize Phoenix, Docker

### Phase Ordering Rationale

- **Data dependency chain drives order:** Ingestion → Retrieval → Generation is a hard dependency chain. You cannot test downstream components without upstream outputs.
- **Differentiators clustered in Phases 2-4:** Hybrid retrieval (Phase 2), citation enforcement (Phase 3), and evaluation gates (Phase 4) are the three features no competitor combines. They get built before any polish.
- **Evaluation before frontend:** Automated eval and CI quality gates (Phase 4) are a stronger portfolio signal than a pretty UI. They must be complete before frontend work begins.
- **Frontend is explicitly last:** The frontend is a consumer, not a differentiator. A working API testable via Swagger UI is sufficient until Phase 5. This prevents scope creep (Pitfall 11).
- **Architecture grows incrementally:** Start with simple structure in Phase 1, grow toward the full domain-package layout by Phase 3 (avoids Pitfall 10).
- **Golden dataset creation starts early:** Begin writing Q&A pairs in Phase 1 (independent of pipeline), execute evaluation in Phase 4.

### Research Flags

Phases likely needing deeper research during planning:
- **Phase 3 (Generation):** Gemini Flash structured output behavior is the biggest unknown. LangChain's `with_structured_output()` for Gemini needs hands-on testing. Citation prompt engineering requires iterative refinement. Recommend `/gsd-research-phase` before detailed task breakdown.
- **Phase 4 (Evaluation):** Ragas 0.4.x API has significant breaking changes from widely-cited tutorials. DeepEval CI integration patterns need validation. Golden dataset design (what makes good adversarial Q&A pairs) benefits from research. Recommend `/gsd-research-phase`.

Phases with standard patterns (skip research-phase):
- **Phase 1 (Ingestion):** Well-documented patterns in LangChain and LlamaIndex. PyMuPDF, RecursiveCharacterTextSplitter, ChromaDB all have mature docs. Standard pipeline pattern.
- **Phase 2 (Retrieval):** RRF fusion is a published algorithm (k=60 default). BM25 is a math algorithm. Cross-encoder reranking via sentence-transformers has clear API. All well-documented.
- **Phase 5 (Frontend):** Standard React + FastAPI integration. No domain-specific complexity.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | All versions verified on PyPI as of 2026-03-04. LangChain 1.x, ChromaDB 1.x, sentence-transformers 5.x all at production/stable. Compatibility matrix validated across all libraries. |
| Features | HIGH | Based on competitor analysis of Verba (7.6k stars), PrivateGPT (57.1k stars), LangChain templates, LlamaIndex docs. Feature prioritization validated against competitive landscape. |
| Architecture | HIGH | Two-pipeline pattern (ingestion + query) is canonical across LangChain, LlamaIndex, and all major RAG frameworks. FastAPI project structure follows official docs. RRF backed by published research. |
| Pitfalls | HIGH | Mix of official documentation (Ragas migration guide, ChromaDB persistence docs, LangChain structured output) and well-documented community experience. All prevention strategies are concrete and actionable. |

**Overall confidence:** HIGH

### Gaps to Address

- **Gemini Flash structured output reliability:** Research identifies this as a risk but exact failure rates are unknown. Need hands-on testing with 50+ varied queries during Phase 3 planning. Monitor parse failure rate.
- **Ragas 0.4.x + Gemini as LLM judge:** Some Ragas metrics may have specific requirements for the evaluation LLM. Test early (smoke test in Phase 2) rather than discovering issues in Phase 4.
- **BM25 index persistence format:** rank-bm25 operates in-memory only. Persistence strategy (pickle, custom serialization) needs validation for restart scenarios and corruption recovery.
- **Evaluation LLM cost at scale:** 50+ golden Q&A × 4 metrics × 3-5 LLM calls = 600-1000 calls per eval run. Free tier feasibility for CI needs real-world timing validation.
- **Qwen 2.5 7B quality as fallback:** Identified as fallback LLM but quality on citation-enforced structured output tasks is unvalidated. May not follow JSON schema as reliably as Gemini Flash.
- **Cross-encoder CPU latency budget:** ms-marco-MiniLM-L-6-v2 reranking on CPU adds 200-500ms/query. Acceptable for portfolio demo but needs benchmarking. ONNX export may improve this 2-3x.

## Sources

### Primary (HIGH confidence)
- **PyPI package metadata** — All library versions and release dates verified directly (2026-03-04)
- **LangChain docs** (python.langchain.com) — RAG tutorial, LCEL, structured output, Gemini integration
- **FastAPI docs** (fastapi.tiangolo.com) — APIRouter pattern, dependency injection, project structure
- **ChromaDB docs** (docs.trychroma.com) — Persistent client, hybrid search, collection management
- **Ragas docs** (docs.ragas.io) — Evaluation metrics, v0.3→v0.4 migration guide, test generation
- **DeepEval docs** (docs.confident-ai.com) — pytest integration, CI/CD patterns, RAG metrics
- **sentence-transformers docs** — v5.x SparseEncoder, CrossEncoder API, model loading
- **Arize Phoenix docs** (docs.arize.com/phoenix) — OpenTelemetry tracing, RAG analysis
- **RRF paper** (Cormack et al., 2009) — Reciprocal Rank Fusion algorithm, k=60 default

### Secondary (MEDIUM confidence)
- **Verba** (github.com/weaviate/Verba, 7.6k stars) — Feature landscape, scope decisions, chunking strategies
- **PrivateGPT** (github.com/zylon-ai/private-gpt, 57.1k stars) — Architecture patterns, API design (OpenAI-compatible)
- **LangChain RAG-from-Scratch** (github.com/langchain-ai/rag-from-scratch) — Multi-query, HyDE, RAG fusion patterns
- **Community consensus** — RAG production failure modes, LLM structured output challenges

### Tertiary (LOW confidence)
- **Qwen 2.5 7B structured output capability** — Inferred from general model benchmarks, not tested for citation-enforced JSON compliance
- **rank-bm25 persistence patterns** — Library is in-memory only; persistence approach requires custom implementation
- **ONNX cross-encoder optimization** — Documented in sentence-transformers but not verified for ms-marco-MiniLM-L-6-v2 specifically

---
*Research completed: 2026-03-04*
*Ready for roadmap: yes*
