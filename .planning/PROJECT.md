# RAGReady

## What This Is

A production-grade Retrieval-Augmented Generation (RAG) system that ingests domain-specific documents (PDF, Markdown, TXT, HTML), retrieves relevant chunks via hybrid search (dense + sparse), and generates grounded, citation-enforced answers. Built as a senior-level portfolio project demonstrating production engineering: automated evaluation pipelines, CI/CD quality gates, observability, and measurable retrieval/generation metrics.

## Core Value

Every generated answer must be grounded in retrieved evidence with verifiable citations — the system refuses to answer rather than hallucinate. If everything else fails, citation-enforced generation with measurable faithfulness must work.

## Requirements

### Validated

(None yet — ship to validate)

### Active

- [ ] Document ingestion pipeline (PDF/MD/TXT/HTML extraction, semantic chunking, dual indexing)
- [ ] Hybrid retrieval with RRF fusion (dense embeddings + BM25, cross-encoder reranking, top-5 results)
- [ ] Citation-enforced generation (structured JSON output with answer + citations[] + confidence, refusal below threshold)
- [ ] Evaluation pipeline (golden dataset 50+ Q&A pairs, Ragas/DeepEval metrics: Faithfulness >0.85, Answer Relevancy >0.80, Context Recall >0.75, Context Precision >0.70)
- [ ] CI/CD quality gates (GitHub Actions, metric thresholds block PRs, eval reports as artifacts)
- [ ] FastAPI backend with query endpoint, health check, and document upload
- [ ] React frontend with chat interface, source panel, and confidence indicators
- [ ] Observability and monitoring (Arize Phoenix or LangSmith, latency/token tracking)
- [ ] Naive vs hybrid benchmark comparison (measurable retrieval quality improvement)
- [ ] Portfolio artifacts (architecture diagram, CI screenshot, evaluation dashboard, 2-min demo video)

### Out of Scope

- Multi-tenant authentication — v1 is single-user, auth adds complexity without demonstrating RAG skills
- Real-time streaming responses — batch response first, streaming is a polish feature
- GraphRAG / knowledge graphs — impressive but overkill for v1, revisit in v2
- Fine-tuned embeddings — use pre-trained all-MiniLM-L6-v2, fine-tuning is a separate project
- Multi-language support — English-only for v1
- Production deployment scaling (k8s, load balancing) — Railway/Render single-instance is sufficient for portfolio

## Context

**Why this project:** Portfolio piece targeting senior ML/AI engineering roles. Demonstrates production mindset: not just "it works" but measurable quality, automated testing, CI/CD, and observability. The RAG domain is hot in 2025-2026 and shows practical LLM engineering skills.

**Senior dev principles driving design:**
- Never trust retrieval — always rerank (cross-encoder after initial retrieval)
- Fail loudly — return null/refusal, never hallucinate
- Version index with DVC — reproducible experiments
- Separate concerns — 4 independent services (ingestion, retrieval, generation, evaluation)
- Golden dataset first — can't improve what you can't measure
- Measure retrieval separately from generation — isolate where quality breaks down

**Architecture overview (5 layers):**
1. **Document Ingestion:** PDF/MD/TXT/HTML → text extraction → semantic chunking (RecursiveCharacterTextSplitter, 512 tokens, 50 overlap) → dual indexing (ChromaDB vectors + BM25 sparse index)
2. **Hybrid Retrieval:** Dense search (all-MiniLM-L6-v2 embeddings) + BM25 sparse search → RRF fusion (k=60) → cross-encoder reranking (ms-marco-MiniLM-L-6-v2) → top-5 results, target 95% precision
3. **Citation-Enforced Generation:** Structured JSON output (answer + citations[] + confidence), temperature 0.0-0.3, refuses to answer below confidence threshold
4. **Evaluation Pipeline:** Ragas/DeepEval framework, golden dataset of 50+ Q&A pairs, custom metrics (Refusal Accuracy >90%, Citation Accuracy >95%)
5. **CI/CD Quality Gates:** GitHub Actions, metric thresholds block PRs, eval reports as artifacts

**Target timeline:** ~5 weeks (Week 1: ingestion, Week 2: retrieval, Week 3: API+UI, Week 4: eval+CI, Week 5: monitoring+polish)

**Deployment target:** Railway or Render (single-instance, free/hobby tier sufficient for portfolio)

## Constraints

- **Tech stack:** Python backend (FastAPI), React frontend, LangChain/LlamaIndex orchestration — user has experience with these
- **LLM:** Gemini Flash (primary, free tier) + local Qwen fallback (offline dev) — cost-conscious, no OpenAI dependency
- **Embeddings:** all-MiniLM-L6-v2 via sentence-transformers — runs locally, no API costs
- **Vector DB:** ChromaDB (dev) / Qdrant (production option) — lightweight, no infrastructure overhead
- **Reranker:** cross-encoder/ms-marco-MiniLM-L-6-v2 — proven quality, runs locally
- **Evaluation:** Ragas + DeepEval — industry standard for RAG evaluation
- **CI/CD:** GitHub Actions — free for public repos
- **Budget:** $0 infrastructure cost target (free tiers, local models where possible)
- **Timeline:** ~5 weeks to portfolio-ready

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Hybrid retrieval (dense + BM25) over dense-only | BM25 catches exact matches dense misses; RRF fusion is proven | — Pending |
| ChromaDB over Pinecone/Weaviate | Local-first, no API costs, sufficient for portfolio scale | — Pending |
| Gemini Flash over OpenAI | Free tier, avoids API cost anxiety during development | — Pending |
| Cross-encoder reranking over no reranking | Dramatically improves precision; ms-marco model is lightweight | — Pending |
| Structured JSON output over free-text | Enables automated citation verification and confidence scoring | — Pending |
| Ragas + DeepEval over custom eval | Industry standard, recognized by hiring managers, good documentation | — Pending |
| FastAPI over Flask/Django | Async support, auto-docs, type hints, modern Python standard | — Pending |
| Monorepo over separate repos | Simpler CI/CD, atomic changes across layers, easier portfolio presentation | — Pending |

---
*Last updated: 2026-03-04 after initialization*
