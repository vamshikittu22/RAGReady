# Feature Landscape

**Domain:** Production RAG System (Senior Portfolio Project)
**Researched:** 2026-03-04
**Overall Confidence:** HIGH

## Table Stakes

Features users/reviewers expect. Missing = system feels like a toy or tutorial project.

| # | Feature | Why Expected | Complexity | Notes |
|---|---------|-------------|------------|-------|
| T1 | **Multi-format document ingestion** (PDF, MD, TXT, HTML) | Every RAG system does this. Verba supports 8+ formats, PrivateGPT handles them all via LlamaIndex. Reviewers will upload their own docs to test. | Medium | PDF parsing is the hard part. Use PyMuPDF or pdfplumber for text extraction. HTML needs tag stripping + content extraction. |
| T2 | **Semantic chunking with configurable strategy** | Naive fixed-size chunking is a tutorial anti-pattern. Verba offers 8 chunking strategies (token, sentence, semantic, recursive, etc.). A senior project must show intentional chunking decisions. | Medium | Implement at least recursive + semantic. Expose chunk_size and chunk_overlap as configurable params. Store chunk metadata (source_doc, page_number, position). |
| T3 | **Vector embedding + dense retrieval** | The literal core of RAG. Every system from PrivateGPT to Verba does this. Without it, there's no RAG. | Low | Use sentence-transformers (all-MiniLM-L6-v2 for dev speed, or a stronger model like BGE/E5 for production quality). Store in a proper vector store. |
| T4 | **LLM-powered answer generation** | Users expect to ask questions and get coherent answers. This is the "G" in RAG. | Low | Use OpenAI API (gpt-4o-mini for cost efficiency, gpt-4o for quality). Abstract behind an interface to swap providers. |
| T5 | **Source attribution / basic citations** | Users must know WHERE an answer came from. Verba shows source chunks, PrivateGPT shows source documents. Without citations, answers are unverifiable black boxes. | Medium | At minimum: show which chunks were used. Better: show document name + page/section. Best: inline citations with chunk quotes. |
| T6 | **REST API backend** | Any production system needs an API. PrivateGPT uses FastAPI following OpenAI's API standard. This is the expected interface pattern. | Low | FastAPI with proper request/response models, error handling, and OpenAPI docs. |
| T7 | **Chat/query UI** | Users need to interact with the system. Verba has a full React UI, PrivateGPT uses Gradio. A portfolio project without a UI is just a script. | Medium | React frontend with a clean chat interface, document upload, and source display panel. |
| T8 | **Document management** (upload, list, delete) | Users need to manage their knowledge base. Every competitor supports CRUD on documents. | Low | API endpoints for upload, list, delete. Frontend file management panel. Track ingestion status per document. |
| T9 | **Basic evaluation metrics** | Without measurable quality, it's a demo not a system. Ragas provides Faithfulness, Context Precision, Answer Relevancy. DeepEval offers 50+ metrics. A senior project must show it can measure itself. | Medium | Run at least Faithfulness + Answer Relevancy on a golden dataset. Report scores in a structured way. |
| T10 | **Configurable retrieval parameters** | Top-k, similarity threshold, etc. Every serious RAG system exposes these. LlamaIndex's RAGs project configures top-k, chunk size, embed model, LLM. | Low | Expose top_k, similarity_threshold, chunk_size in config. Allow adjustment without code changes (env vars or config file). |

## Differentiators

Features that set this project apart from the sea of RAG tutorials and template projects. These are what make a hiring manager pause and say "this person understands production AI."

| # | Feature | Value Proposition | Complexity | Notes |
|---|---------|-------------------|------------|-------|
| D1 | **Hybrid retrieval (dense + BM25 with RRF fusion)** | Most tutorial RAG projects use ONLY dense retrieval. Hybrid search is what production systems actually use. Verba lists it as a core feature but many OSS projects skip it. Shows understanding that dense retrieval fails on keyword-specific queries (IDs, exact terms, acronyms). | Medium | BM25 via rank_bm25 or Elasticsearch. RRF (Reciprocal Rank Fusion) with k=60 is the standard fusion method. Must demonstrate measurable improvement over dense-only in benchmarks. |
| D2 | **Cross-encoder reranking** | Bi-encoder retrieval is fast but imprecise. Cross-encoder reranking is the production pattern (Cohere, Google, Microsoft all use it). Verba lists reranking as "planned" - building it shows you're ahead. LlamaIndex documents this as a Node Postprocessor pattern. | Medium | Use cross-encoder/ms-marco-MiniLM-L-6-v2 from sentence-transformers. Retrieve top-20, rerank to top-5. Measurable precision improvement. |
| D3 | **Citation-enforced structured output** (JSON: answer + citations[] + confidence) | This is the killer differentiator. Most RAG projects return plain text. Structured output with verifiable citations and confidence scores shows production thinking. The "refuse to answer below threshold" behavior demonstrates responsible AI design. | High | Use structured output (Pydantic models) to enforce JSON schema: `{answer, citations: [{text, source, page, score}], confidence, refusal_reason?}`. Confidence threshold triggers refusal. |
| D4 | **Naive vs. hybrid benchmark comparison** | Proves engineering decisions with data, not vibes. Shows the reviewer exactly WHY hybrid search matters through side-by-side evaluation. This is what "data-driven engineering" looks like on a resume. | Medium | Run identical golden dataset queries through naive (dense-only, no reranking) vs. full pipeline. Compare Faithfulness, Answer Relevancy, Context Precision. Present as a table/chart. |
| D5 | **Automated evaluation pipeline** (golden dataset, Ragas/DeepEval, CI gates) | Most portfolio RAG projects have zero evaluation. Adding automated eval with quality gates shows ML engineering maturity. Ragas and DeepEval both support CI/CD integration (DeepEval has pytest-style assertions, Ragas has CLI evaluation). | High | 50+ golden Q&A pairs. Ragas metrics: Faithfulness >0.85, Answer Relevancy >0.80. Run in GitHub Actions. Block PRs that regress metrics. |
| D6 | **CI/CD quality gates that block on metric regression** | Takes D5 further by making evaluation a hard gate, not just a report. This is the pattern companies like Uber, Airbnb use for ML systems in production. DeepEval explicitly supports "unit testing in CI/CD." | Medium | GitHub Actions workflow that runs eval suite on PR. If Faithfulness drops below threshold, PR is blocked. Screenshot of a blocked PR is a powerful portfolio artifact. |
| D7 | **Observability integration** (Arize Phoenix or LangSmith tracing) | Production AI systems need tracing. Phoenix provides: LLM traces with span-level visibility, auto-instrumentation for LlamaIndex/LangChain, evaluation scoring on traces, prompt iteration from real examples. This shows you think about debugging and monitoring, not just building. | Medium | Arize Phoenix is free, self-hosted, and built on OpenTelemetry. Instrument the full RAG pipeline: retrieval latency, LLM token usage, chunk relevance scores. |
| D8 | **Semantic chunking with overlap + metadata enrichment** | Going beyond basic chunking to add structured metadata (document title, section headers, page numbers, creation date). LlamaIndex documents metadata extraction as a key indexing feature. This metadata powers better retrieval and richer citations. | Medium | Extract document-level metadata during ingestion. Add section hierarchy for MD/HTML. Tag chunks with structural context. |
| D9 | **Portfolio artifacts** (architecture diagram, CI screenshot, eval dashboard, demo video) | Not a software feature, but a presentation feature that is table-stakes for a portfolio project targeting ML/AI roles. Without clear visuals, even a great system gets overlooked. | Low | Architecture diagram (Mermaid or draw.io), eval dashboard (can be a simple HTML page or Streamlit), 2-min Loom demo, CI badge in README. |
| D10 | **Query preprocessing** (query expansion or HyDE) | Advanced retrieval technique. LangChain's RAG-from-scratch covers multi-query expansion and HyDE (Hypothetical Document Embeddings). Shows deep understanding of retrieval challenges (vocabulary mismatch, ambiguous queries). | Medium | Implement one of: multi-query (generate 3 rephrased queries, union results), step-back prompting, or HyDE. Show retrieval improvement in benchmarks. |

## Anti-Features

Features to explicitly NOT build in v1. Scope control is itself a senior engineering skill.

| # | Anti-Feature | Why Avoid | What to Do Instead |
|---|-------------|-----------|-------------------|
| A1 | **Multi-tenant authentication / RBAC** | Adds massive complexity (user management, document isolation, permission models) with zero ML/AI learning value. PrivateGPT doesn't even support multiple users. Verba explicitly marks multi-user as "out of scope." | Single-user system. Mention in README that multi-tenancy is a v2 consideration. |
| A2 | **Real-time streaming responses** | SSE/WebSocket streaming is a UX nicety that adds frontend complexity without demonstrating AI engineering skills. It's plumbing, not ML. | Return complete responses. Note in architecture doc that streaming can be added via FastAPI StreamingResponse. |
| A3 | **GraphRAG / Knowledge Graph construction** | Entirely different architecture pattern. Both Verba and PrivateGPT list GraphRAG as "out of scope." It requires entity extraction, relation modeling, graph databases - each a project unto itself. | Mention awareness of GraphRAG in architecture docs as a future direction. Focus on proving hybrid vector search excellence first. |
| A4 | **Fine-tuned embedding models** | Training custom embeddings requires labeled data, GPU infrastructure, evaluation pipelines - it's a separate ML project. Pretrained models (BGE, E5, all-MiniLM) are excellent for this use case. | Use strong pretrained embeddings. Document model selection rationale. |
| A5 | **Multi-language support** | Adds testing complexity across languages. Embedding model behavior varies by language. Chunking strategies differ. Not worth the scope for a portfolio project. | English-only. Note that multilingual embeddings (e.g., multilingual-e5) could enable this in v2. |
| A6 | **Agentic RAG / Multi-step reasoning** | Adds autonomous decision-making complexity. Verba explicitly marks Agentic RAG as "out of scope." It requires tool selection, planning, error recovery - orthogonal to demonstrating retrieval quality. | Direct query-retrieve-generate pipeline. Clean, understandable, debuggable. Mention agents as a v2 extension. |
| A7 | **Custom UI component library / Design system** | Over-investing in frontend polish steals time from the ML differentiation. The UI should be clean and functional, not award-winning. | Use a component library (shadcn/ui, MUI) for rapid, clean UI. Focus design time on the source citation panel and eval dashboard. |
| A8 | **Production-scale infrastructure** (Kubernetes, auto-scaling, load balancing) | Overengineering for a portfolio project. No reviewer will test at 1000 QPS. Docker Compose is sufficient. | Docker Compose for local deployment. Document how it WOULD scale (architecture doc) without building it. |
| A9 | **Multi-modal ingestion** (images, audio, video) | Requires OCR, speech-to-text, frame extraction - each a complex pipeline. Verba uses AssemblyAI for audio; it's substantial integration work. | Text-based documents only. PDF text extraction (not OCR on scanned PDFs). |
| A10 | **Conversation memory / Multi-turn chat** | Adds state management complexity without demonstrating core RAG skills. Single-turn Q&A is sufficient to demonstrate retrieval + generation quality. | Single-turn queries. Each query is independent. Note in docs that conversation history can be added via chat buffer. |

## Feature Dependencies

```
Document Ingestion (T1)
  |
  v
Chunking Strategy (T2)
  |
  +--> Dense Embedding + Indexing (T3) --+
  |                                       |
  +--> BM25 Sparse Indexing (D1) --------+
                                          |
                                          v
                                 Hybrid Retrieval + RRF Fusion (D1)
                                          |
                                          v
                                 Cross-Encoder Reranking (D2)
                                          |
                                          v
                            Citation-Enforced Generation (D3) <-- LLM (T4)
                                          |
                                          v
                              Structured JSON Response (D3)
                                    |           |
                                    v           v
                              REST API (T6)   Frontend (T7)
                                    |
                                    v
                      Observability / Tracing (D7)

Golden Dataset (standalone)
  |
  v
Evaluation Pipeline (D5) --> Naive vs Hybrid Benchmark (D4)
  |
  v
CI/CD Quality Gates (D6)
  |
  v
Portfolio Artifacts (D9)
```

### Dependency Notes

1. **T1 -> T2 -> T3**: Document ingestion must work before chunking, chunking before embedding. This is the core pipeline and should be built first.
2. **D1 depends on T2**: BM25 indexing requires chunked documents. Must be built after basic dense retrieval works.
3. **D2 depends on D1**: Reranking operates on the merged result set from hybrid retrieval.
4. **D3 depends on T4 + D2**: Citation enforcement requires both reranked chunks and LLM generation. This is the integration point.
5. **D5 can be started early**: Golden dataset creation is independent of pipeline implementation. Start writing Q&A pairs while building ingestion.
6. **D6 depends on D5**: CI gates need the evaluation pipeline to exist first.
7. **D7 (observability) is parallel**: Can be instrumented at any point once the API exists. Add it incrementally as components are built.
8. **D4 depends on D1 + D5**: Benchmark comparison requires both the naive and hybrid pipelines plus the evaluation framework.

## MVP Recommendation

### Launch With (v1 - Target)

This is the full v1 scope as described in the project context. Build in this order:

**Phase 1: Foundation (Document Pipeline)**
1. T1 - Multi-format document ingestion (PDF, MD, TXT, HTML)
2. T2 - Semantic/recursive chunking with metadata
3. T3 - Dense vector embedding + indexing
4. T8 - Document management (upload, list, delete)

**Phase 2: Retrieval Excellence**
5. D1 - Hybrid retrieval (BM25 + dense + RRF fusion)
6. D2 - Cross-encoder reranking
7. T10 - Configurable retrieval parameters

**Phase 3: Generation + Citations**
8. T4 - LLM answer generation
9. D3 - Citation-enforced structured output (the killer feature)
10. T5 - Source attribution in responses

**Phase 4: Evaluation + Quality**
11. T9 - Basic evaluation metrics
12. D5 - Automated evaluation pipeline (golden dataset, Ragas)
13. D4 - Naive vs hybrid benchmark comparison
14. D6 - CI/CD quality gates

**Phase 5: Interface + Observability**
15. T6 - FastAPI REST API
16. T7 - React chat UI with source panel
17. D7 - Observability (Arize Phoenix)

**Phase 6: Polish + Portfolio**
18. D9 - Portfolio artifacts (architecture diagram, demo video, eval dashboard)
19. D8 - Metadata enrichment refinement

### Add After Validation (v1.x)

These features would strengthen the project further but should only be attempted after v1 is solid:

| Feature | Rationale for Deferral |
|---------|----------------------|
| D10 - Query preprocessing (HyDE/multi-query) | Nice retrieval improvement, but only valuable once baseline retrieval metrics are already good. |
| Streaming responses | UX polish after core is proven. FastAPI StreamingResponse is straightforward. |
| Conversation memory | Single-turn is sufficient for v1 portfolio. Chat history adds state management complexity. |
| Additional file formats (DOCX, CSV) | Low-hanging fruit to add once ingestion pipeline is stable. |
| Prompt versioning / A-B testing | Shows advanced prompt engineering. Arize Phoenix supports prompt iteration. |

### Future (v2+)

| Feature | Why v2 |
|---------|--------|
| Multi-tenant / RBAC | Completely different domain (auth/authz), not ML engineering |
| GraphRAG hybrid | Requires graph DB, entity extraction - separate project |
| Agentic RAG with tool use | Builds on v1 retrieval but adds autonomous reasoning |
| Fine-tuned embeddings | Requires labeled data + GPU training |
| Multi-language support | Needs multilingual embedding models + evaluation |
| Multi-modal (images, tables) | OCR, layout analysis, table extraction |

## Feature Prioritization Matrix

| Feature | Impact on Portfolio | Implementation Effort | Risk | Priority |
|---------|--------------------|-----------------------|------|----------|
| D3 - Citation-enforced generation | **Critical** - The single most differentiating feature | High | Medium (structured output parsing can be finicky) | P0 |
| D5 - Automated evaluation pipeline | **Critical** - Proves ML engineering maturity | High | Low (Ragas/DeepEval are well-documented) | P0 |
| D1 - Hybrid retrieval (RRF) | **High** - Shows production-grade retrieval | Medium | Low (well-established pattern) | P0 |
| D6 - CI/CD quality gates | **High** - Visible proof of engineering rigor | Medium | Low (GitHub Actions is standard) | P0 |
| D4 - Naive vs hybrid benchmark | **High** - Data-driven decision evidence | Medium | Low (comparison after both pipelines exist) | P1 |
| D2 - Cross-encoder reranking | **High** - Shows retrieval depth | Medium | Low (sentence-transformers models are mature) | P1 |
| D7 - Observability (Phoenix) | **Medium** - Shows production thinking | Medium | Low (Phoenix has good Python integration) | P1 |
| T7 - React frontend | **Medium** - Needed for demo but not the differentiator | Medium | Medium (frontend complexity) | P1 |
| D9 - Portfolio artifacts | **Medium** - Necessary for presentation | Low | Low | P2 |
| D10 - Query preprocessing | **Low** - Nice to have, not expected | Medium | Medium (must prove it actually helps) | P3 |

## Competitor Feature Analysis

| Feature | RAGReady (v1 Target) | Verba (Weaviate) | PrivateGPT (Zylon) | LangChain RAG Templates | LlamaIndex RAGs |
|---------|---------------------|-----------------|-------------------|------------------------|----------------|
| **Multi-format ingestion** | PDF, MD, TXT, HTML | PDF, CSV, DOCX, GitHub, audio, URLs | PDF, TXT, via LlamaIndex loaders | Varies by template | User configurable |
| **Chunking strategies** | Recursive + Semantic | Token, Sentence, Semantic, Recursive, HTML, MD, Code, JSON (8 types) | Via LlamaIndex node parsers | Basic recursive | Configurable via UI |
| **Dense retrieval** | Yes | Yes | Yes (LlamaIndex VectorStore) | Yes | Yes |
| **Hybrid retrieval (BM25+dense)** | Yes (RRF fusion) | Yes | No (single retrieval mode) | Some templates | No |
| **Cross-encoder reranking** | Yes | Planned (not yet) | No | Some templates | No (configurable) |
| **Citation-enforced structured output** | Yes (JSON schema with confidence + refusal) | No (shows source chunks only) | No (shows source docs) | No | No |
| **Confidence-based refusal** | Yes (below threshold = refuse) | No | No | No | No |
| **Automated evaluation (Ragas/DeepEval)** | Yes (CI/CD integrated) | Planned (not yet) | No | No | No |
| **CI/CD quality gates** | Yes (GitHub Actions blocks on regression) | No | No | No | No |
| **Observability / Tracing** | Yes (Arize Phoenix) | No | No | LangSmith (optional) | LlamaIndex callbacks |
| **Naive vs Hybrid benchmark** | Yes (side-by-side comparison) | No | No | No | No |
| **Architecture documentation** | Yes (diagram + technical docs) | Yes (TECHNICAL.md) | Yes (Fern docs) | Notebooks only | README only |
| **Docker deployment** | Yes (Docker Compose) | Yes | Yes | No | No |
| **Multi-tenant / Auth** | No (out of scope) | No (out of scope) | No | No | No |
| **GraphRAG** | No (out of scope) | No (out of scope) | No | No | No |
| **Stars/Popularity** | Portfolio project | 7.6k | 57.1k | Varies | 6.5k |

### Competitive Positioning Summary

RAGReady's differentiation comes from three areas none of the competitors combine:

1. **Citation-enforced structured output with confidence-based refusal** - No competitor does this. Verba and PrivateGPT show source chunks but don't enforce citation structure or refuse low-confidence answers. This is the "responsible AI" differentiator.

2. **Automated evaluation with CI/CD gates** - Verba and PrivateGPT list evaluation as "planned." RAGReady ships with a golden dataset, Ragas metrics, and GitHub Actions gates that block regressions. This is the "ML engineering" differentiator.

3. **Data-driven architecture decisions** - The naive vs. hybrid benchmark comparison proves with data why each architectural choice was made. No competitor provides this. This is the "engineering judgment" differentiator.

The combination signals: "I don't just build RAG systems, I build RAG systems that measure themselves, prove their decisions with data, and refuse to hallucinate."

## Sources

- **Ragas Documentation** (https://docs.ragas.io/en/stable/) - Evaluation metrics: Faithfulness, Context Precision, Context Recall, Answer Relevancy. Supports test data generation. Integrates with LangChain, LlamaIndex. [HIGH confidence]
- **DeepEval Documentation** (https://docs.confident-ai.com/docs/getting-started) - 50+ LLM evaluation metrics. CI/CD unit testing support via pytest. RAG-specific metrics (AnswerRelevancy, Faithfulness, Contextual Recall, Contextual Precision). Synthetic data generation. [HIGH confidence]
- **Verba (Weaviate)** (https://github.com/weaviate/Verba) - v2.1.3, 7.6k stars. 8 chunking strategies, hybrid search, multiple LLM/embedding providers. Reranking and evaluation are "planned." Multi-user and GraphRAG are "out of scope." [HIGH confidence]
- **PrivateGPT (Zylon)** (https://github.com/zylon-ai/private-gpt) - v0.6.2, 57.1k stars. FastAPI + LlamaIndex. OpenAI-compatible API. High-level RAG API + low-level primitives. Privacy-focused (100% local option). No evaluation, no hybrid search, no reranking. [HIGH confidence]
- **LangChain RAG-from-Scratch** (https://github.com/langchain-ai/rag-from-scratch) - Educational notebooks covering indexing, retrieval, generation, multi-query, RAG fusion, decomposition, step-back, HyDE. [HIGH confidence]
- **Arize Phoenix** (https://docs.arize.com/phoenix) - AI observability platform. Tracing via OpenTelemetry/OpenInference. Auto-instrumentation for LlamaIndex, LangChain. Evaluation scoring on traces. Prompt engineering with replay. Self-hostable. [HIGH confidence]
- **LlamaIndex Framework** (https://docs.llamaindex.ai/) - Node parsers (chunking), VectorStoreIndex, node postprocessors (reranking), response synthesizers, evaluation modules, metadata extraction. [HIGH confidence]
