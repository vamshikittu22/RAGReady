# Domain Pitfalls

**Domain:** Production RAG System (Retrieval-Augmented Generation)
**Researched:** 2026-03-04
**Overall Confidence:** HIGH

---

## Critical Pitfalls

Mistakes that cause rewrites, missed deadlines, or fundamentally broken systems.

### Pitfall 1: Trusting LLM Output Format Without Validation

**What goes wrong:** The LLM returns malformed JSON, hallucinated citation IDs, or inconsistent field names. The system crashes or silently produces garbage.

**Why it happens:** LLMs are probabilistic. Even with structured output prompts, Gemini Flash and Qwen will occasionally return invalid JSON, especially with complex schemas. Temperature 0.0 reduces but does not eliminate this.

**Consequences:** Frontend crashes on malformed responses. Users see hallucinated citations pointing to non-existent chunks. Trust in the system erodes immediately.

**Prevention:**
1. Always parse LLM responses through Pydantic models — never `json.loads()` alone.
2. Validate every citation `chunk_id` against the actually-retrieved chunks.
3. Implement retry logic (1 retry with explicit format reminder in the prompt).
4. If retry fails, return a structured refusal response (not an error/crash).
5. Use LangChain's `PydanticOutputParser` or `with_structured_output()` for Gemini.

**Detection:** Unit tests with deliberately malformed LLM responses. Integration tests that verify citation IDs match retrieved chunks. Monitor parse failure rate in observability.

---

### Pitfall 2: BM25 Index / ChromaDB Index Desynchronization

**What goes wrong:** Documents are added to ChromaDB (dense index) but not the BM25 index (or vice versa). Hybrid retrieval returns inconsistent results.

**Why it happens:** Dual indexing means two write paths. If ingestion fails midway (e.g., BM25 indexing crashes after ChromaDB succeeds), the indexes diverge. No transaction coordination between ChromaDB and the in-memory BM25 store.

**Consequences:** Queries return results from one index that don't exist in the other. RRF fusion operates on different document sets. Retrieval quality silently degrades. Very hard to debug because the system "works" but quality is wrong.

**Prevention:**
1. Wrap dual indexing in a single `ingest()` function that indexes to BOTH stores atomically.
2. Add a `verify_sync()` function that compares document counts and IDs across both indexes.
3. Run `verify_sync()` at startup and after each ingestion batch.
4. If desync detected, re-index from source documents (idempotent ingestion).
5. Store a shared document manifest (document_id → chunk_ids) that both indexes reference.

**Detection:** Health check endpoint that reports index sizes. Logging that counts chunks written to each index per ingestion. Startup verification.

---

### Pitfall 3: Ragas/DeepEval API Breaking Changes

**What goes wrong:** Tutorials and examples use Ragas 0.2.x APIs. Ragas 0.4.x has breaking changes. You copy example code, it doesn't work, you spend hours debugging import errors and API mismatches.

**Why it happens:** Ragas jumped from 0.2.x → 0.4.x with significant API changes (new `llm_factory`, `AspectCritic` for custom metrics, changed evaluation function signatures). Most blog posts and tutorials still reference 0.2.x patterns. DeepEval v3.x also changed substantially from v2.x.

**Consequences:** Lost development time debugging framework mismatches. Evaluation pipeline doesn't work in CI. Quality gates are the differentiator — if they don't work, the project loses its edge.

**Prevention:**
1. Pin exact versions in requirements.txt (`ragas==0.4.3`, `deepeval==3.8.8`).
2. ONLY reference official docs at `docs.ragas.io/en/latest/` and `docs.confident-ai.com/`.
3. Check the Ragas migration guide: `docs.ragas.io/en/latest/howtos/migrations/migrate_from_v03_to_v04/`.
4. Write a minimal "smoke test" for the eval pipeline early (Phase 1 or 2, not Phase 4).
5. If using Gemini as the evaluation LLM judge, test early — some Ragas metrics require specific LLM capabilities.

**Detection:** CI will catch import errors. But silent API behavior changes (e.g., metric score interpretation) require comparing results against known golden answers.

---

### Pitfall 4: Gemini Flash Free Tier Rate Limits and Downtime

**What goes wrong:** Development stalls because Gemini Flash hits rate limits (60 RPM) or Google's API has an outage. CI pipeline fails because evaluation requires many LLM calls (Ragas runs 3-5x LLM calls per metric per sample).

**Why it happens:** $0 budget means relying entirely on free tiers. Evaluation with 50+ golden Q&A pairs × 4 metrics × 3-5 LLM calls per metric = 600-1000 LLM calls per eval run. At 60 RPM, that's 10-17 minutes minimum, and any rate limit error restarts the batch.

**Consequences:** CI builds take 15+ minutes for evaluation alone. Rate limit errors cause flaky CI. Development is blocked during API outages. Evaluation costs are invisible but real (hitting free tier limits).

**Prevention:**
1. Implement exponential backoff with `tenacity` for all Gemini API calls.
2. Use Qwen (local via Ollama) as the evaluation LLM judge for local development.
3. Only run full Gemini-based eval in CI on PR merges, not on every push.
4. Cache evaluation results — if golden dataset and pipeline haven't changed, skip re-evaluation.
5. Consider batch API calls where possible to reduce RPM.
6. Keep a small "smoke" golden dataset (5-10 pairs) for fast iteration.

**Detection:** Monitor API call counts in CI logs. Set up alerts for rate limit errors. Track CI build time trends.

---

### Pitfall 5: Chunking Strategy Destroys Context

**What goes wrong:** Chunks split in the middle of sentences, tables, code blocks, or logical arguments. Retrieved chunks are individually meaningless. Generation quality is terrible because context is fragmented.

**Why it happens:** Fixed-size chunking (by character count) doesn't respect semantic boundaries. Even RecursiveCharacterTextSplitter has limits — it splits on separators (`\n\n`, `\n`, `. `, ` `) but can still fragment complex content like tables, lists, or multi-paragraph arguments.

**Consequences:** The retriever returns top-5 chunks that are individually relevant but collectively fragmented. The LLM generates an answer from fragments, producing incoherent responses. Citation accuracy drops because chunks don't represent complete thoughts.

**Prevention:**
1. Use RecursiveCharacterTextSplitter with `separators=["\n\n", "\n", ". ", " "]` — paragraph boundaries first.
2. Set chunk overlap to 50 tokens (not 0) — overlap preserves context at boundaries.
3. Store `parent_doc_id` and `position_in_doc` for each chunk — enables context window expansion if needed.
4. Test chunking manually on representative documents before building the rest of the pipeline.
5. Consider document-type-specific chunking (e.g., Markdown headers as split points for .md files).

**Detection:** Manually inspect 20-30 random chunks from each document type. Check: Does each chunk make sense as a standalone text? Are table rows split across chunks? Are code blocks fragmented?

---

## Moderate Pitfalls

### Pitfall 6: Cross-Encoder Reranker Latency

**What goes wrong:** Cross-encoder reranking adds 200-500ms per query on CPU. Total query latency exceeds 3 seconds, making the UI feel sluggish.

**Prevention:**
1. Only rerank top-20 candidates (not all retrieved documents).
2. Use the smallest effective cross-encoder model (ms-marco-MiniLM-L-6-v2 is ~80MB, fast on CPU).
3. Measure reranker latency separately in observability. If too slow, consider reducing to top-10 input candidates.
4. Pre-load the cross-encoder model at startup (not on first request).

---

### Pitfall 7: ChromaDB Persistence Issues

**What goes wrong:** ChromaDB data is lost between restarts, or persistence mode causes file locking issues.

**Prevention:**
1. Use `chromadb.PersistentClient(path="./data/indexes/chroma")` — NOT `chromadb.Client()` (which is ephemeral).
2. Never run multiple processes against the same persistent directory simultaneously.
3. ChromaDB v1.x has improved persistence significantly — but test backup/restore procedures early.
4. In Docker, mount the persistence directory as a volume.

---

### Pitfall 8: Embedding Model / Retrieval Model Mismatch

**What goes wrong:** Index is built with one embedding model but queries use a different one. Results are garbage because vector dimensions or semantic spaces don't match.

**Prevention:**
1. Store the embedding model name as metadata in the ChromaDB collection.
2. Verify at startup that the configured embedding model matches the indexed model.
3. If the model changes, re-index everything (make re-indexing a CLI command: `scripts/ingest.py --force`).
4. Never change `embedding_model` in config without re-indexing.

---

### Pitfall 9: Evaluation Metrics Don't Reflect Real Quality

**What goes wrong:** Ragas Faithfulness is 0.92 but the system still gives bad answers. Metrics are green but users are unhappy.

**Prevention:**
1. Use MULTIPLE metrics — Faithfulness alone is insufficient. Combine with Answer Relevancy, Context Recall, Context Precision.
2. Add custom metrics: Refusal Accuracy (does it refuse when it should?), Citation Accuracy (do citations actually support the answer?).
3. Include adversarial queries in the golden dataset — questions the system SHOULD refuse.
4. Manually validate a sample of responses periodically, not just trust automated metrics.
5. DeepEval's `AnswerRelevancy` and Ragas's `Faithfulness` measure different things — understand what each metric captures.

---

### Pitfall 10: Overcomplicated Project Structure Too Early

**What goes wrong:** Spending 2-3 days setting up the perfect project structure, CI/CD, Docker, DVC, linting, typing, pre-commit hooks... before writing any RAG logic. Then running out of time for the actual differentiating features.

**Prevention:**
1. Phase 1 should produce a WORKING ingestion pipeline, not a perfect project skeleton.
2. Start with a flat structure if needed — refactor into the full structure in Phase 2 or 3.
3. Add CI in Phase 4, not Phase 1. Ruff + mypy can be local-only initially.
4. DVC is Phase 4. Docker is Phase 5. Don't set these up until you need them.
5. The architecture doc (ARCHITECTURE.md) has the target structure — grow toward it, don't build the entire scaffold on day one.

---

### Pitfall 11: Frontend Scope Creep

**What goes wrong:** Spending 5+ days on a beautiful frontend with animations, dark mode, responsive design, document previews... while the evaluation pipeline is incomplete. The frontend is impressive but the portfolio lacks the engineering differentiators.

**Prevention:**
1. Frontend is Phase 5 (last phase). It must be functional, not beautiful.
2. Use Tailwind CSS with a component library (shadcn/ui) for rapid development.
3. Target: chat interface + source panel + confidence indicator + document upload. That's it.
4. 2-3 days maximum on frontend, including API integration.
5. The evaluation pipeline, CI quality gates, and benchmark comparison are the differentiators — frontend is presentation.

---

### Pitfall 12: Gemini Structured Output Inconsistency

**What goes wrong:** Gemini Flash sometimes ignores structured output instructions, returns plain text instead of JSON, or hallucinates extra fields not in the schema.

**Prevention:**
1. Use LangChain's `with_structured_output()` method — it handles the Gemini-specific structured output API.
2. Include the JSON schema explicitly in the system prompt as a backup.
3. Implement a parsing fallback: try Pydantic validation → try regex extraction of JSON from text → refuse.
4. Test structured output with 50+ varied queries to understand failure modes before building the full pipeline.
5. Temperature 0.0-0.1 significantly improves format consistency.

---

## Minor Pitfalls

### Pitfall 13: Python Virtual Environment Conflicts

**What goes wrong:** sentence-transformers, PyMuPDF, and ChromaDB have overlapping transitive dependencies (numpy, scipy, tokenizers). Pip fails to resolve, or resolves to incompatible versions.

**Prevention:**
1. Use a locked dependency resolver: `uv pip install` or `pip-compile` from `pip-tools`.
2. Pin major versions in `requirements.txt`, let the resolver handle minor versions.
3. Test a fresh `pip install` from `requirements.txt` in CI — catches resolution failures early.
4. Consider `pyproject.toml` with `uv` for modern dependency management.

---

### Pitfall 14: Git Repository Bloat from Indexes/Models

**What goes wrong:** Committing ChromaDB index files, BM25 pickle files, or downloaded model weights to git. Repository grows to 500MB+, clones take forever.

**Prevention:**
1. `.gitignore` all of: `data/indexes/`, `data/raw/`, `*.pkl`, `*.bin`, model cache directories.
2. Use DVC for index versioning (track with DVC, store on a free remote like Google Drive).
3. Model weights are downloaded at runtime by sentence-transformers — never commit them.
4. Add max file size check in pre-commit hooks.

---

### Pitfall 15: Inconsistent Chunk IDs Between Sessions

**What goes wrong:** Chunk IDs are generated randomly (UUID4). If you re-index documents, all chunk IDs change. Golden dataset references old chunk IDs. Citation validation breaks.

**Prevention:**
1. Generate deterministic chunk IDs: `hash(document_path + chunk_position + content_hash)`.
2. Or use content-based hashing: `hashlib.sha256(chunk_text.encode()).hexdigest()[:16]`.
3. Golden dataset should reference query-answer pairs, not specific chunk IDs. Chunk IDs are implementation details.
4. Citation validation checks that cited chunk IDs exist in the CURRENT retrieval results, not in a historical index.

---

### Pitfall 16: Forgetting to Handle Empty Retrieval Results

**What goes wrong:** A query returns 0 chunks from retrieval (completely out-of-domain question). The generator receives an empty context and either crashes or hallucinates entirely.

**Prevention:**
1. Check `len(retrieved_chunks) == 0` before calling the generator.
2. If no chunks retrieved, return a refusal response immediately — don't send an empty context to the LLM.
3. If fewer than `final_top_k` chunks retrieved, still proceed but lower the confidence threshold proportionally.
4. Include out-of-domain queries in the golden dataset to test this path.

---

## Phase-Specific Warnings

| Phase | Likely Pitfall | Mitigation |
|-------|---------------|------------|
| **Phase 1: Ingestion** | Pitfall 5 (chunking destroys context), Pitfall 10 (over-engineering structure) | Manually inspect chunks before proceeding. Start simple, refactor later. |
| **Phase 1: Ingestion** | Pitfall 14 (git bloat from indexes) | Set up `.gitignore` for `data/` on day one. |
| **Phase 2: Retrieval** | Pitfall 2 (index desync), Pitfall 6 (reranker latency) | Build `verify_sync()` function. Benchmark reranker latency early. |
| **Phase 2: Retrieval** | Pitfall 8 (model mismatch) | Store embedding model name in collection metadata. |
| **Phase 3: Generation** | Pitfall 1 (trusting LLM output), Pitfall 12 (Gemini structured output) | Pydantic validation + retry logic. Test structured output extensively. |
| **Phase 3: Generation** | Pitfall 16 (empty retrieval) | Handle 0-chunk edge case before generator. |
| **Phase 4: Evaluation** | Pitfall 3 (Ragas/DeepEval breaking changes), Pitfall 4 (rate limits) | Pin versions. Use local LLM for dev eval. Cache results. |
| **Phase 4: Evaluation** | Pitfall 9 (metrics don't reflect quality) | Multiple metrics + manual spot checks + adversarial queries. |
| **Phase 4: Evaluation** | Pitfall 15 (inconsistent chunk IDs) | Deterministic IDs or content-based hashing. |
| **Phase 5: Frontend** | Pitfall 11 (scope creep) | Time-box to 2-3 days. Functional > beautiful. |

---

## Sources

- LangChain structured output documentation — Pydantic output parsers, `with_structured_output()` method [HIGH confidence]
- Ragas migration guide v0.3→v0.4 — API breaking changes documentation [HIGH confidence]
- ChromaDB v1.x docs — persistence client API, collection management [HIGH confidence]
- DeepEval v3.x docs — pytest integration, CI/CD patterns [HIGH confidence]
- FastAPI dependency injection docs — `Depends()` pattern, startup events [HIGH confidence]
- Community experience — RAG production failure modes commonly discussed in LangChain, LlamaIndex, and ML engineering communities [MEDIUM confidence]
- sentence-transformers v5.x — CrossEncoder API, model loading patterns [HIGH confidence]
- Google Gemini free tier documentation — rate limits (60 RPM), structured output capabilities [HIGH confidence]
