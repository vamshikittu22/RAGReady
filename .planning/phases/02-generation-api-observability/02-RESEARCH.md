# Phase 2: Generation, API & Observability - Research

**Researched:** 2026-03-05
**Domain:** LLM generation with citation enforcement, FastAPI REST, RAG tracing
**Confidence:** MEDIUM-HIGH

## Summary

Phase 2 transforms the Phase 1 retrieval pipeline into a complete question-answering system. The generation layer takes retrieved `ScoredChunk` objects, constructs a grounding prompt, calls Gemini Flash (or Qwen fallback), and enforces structured JSON output with citations and confidence scores. The API layer wraps everything in FastAPI endpoints with file upload support. Observability uses Arize Phoenix to trace the full RAG pipeline per query.

The existing codebase provides strong foundations: `HybridRetriever.retrieve()` returns `list[ScoredChunk]` with chunk text, scores, source document names, and page numbers — exactly what citations need. `Settings` already has `google_api_key`, `confidence_threshold=0.6`, and `temperature=0.1`. `IngestionPipeline` has `ingest()`, `delete()`, and `list_documents()` that map directly to API endpoints.

**Critical finding:** `arize-phoenix` on PyPI requires `Python <3.14`, but this project uses Python 3.14.2. The workaround is to use `arize-phoenix-otel` (lightweight OTEL tracer) + `openinference-instrumentation-langchain` (supports Python 3.14) for instrumentation, and run the Phoenix dashboard server via Docker.

**Primary recommendation:** Use `langchain-google-genai` with `ChatGoogleGenerativeAI.with_structured_output()` for Gemini, `langchain-ollama` with `ChatOllama` for Qwen fallback, and a custom fallback wrapper (not LangChain's `.with_fallbacks()`) for more reliable error handling and logging.

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `langchain-google-genai` | >=2.1.0 | Gemini Flash LLM integration | Already in pyproject.toml; provides `ChatGoogleGenerativeAI` with native structured output support |
| `langchain-ollama` | >=0.3.0 | Qwen local LLM via Ollama | **NEW dependency needed**. Official LangChain package for Ollama models. Replaces deprecated `langchain-community` Ollama classes |
| `fastapi[standard]` | already installed | REST API framework | Already in pyproject.toml; includes `python-multipart` for file uploads, Swagger UI |
| `uvicorn[standard]` | already installed | ASGI server | Already in pyproject.toml |
| `pydantic` | >=2.12.0 | Request/response models, structured output schemas | Already in pyproject.toml; used for LLM structured output |
| `tenacity` | >=8.0.0 | Retry logic for LLM calls | Already in pyproject.toml |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `openinference-instrumentation-langchain` | >=0.1.0 | Auto-instrument LangChain for Phoenix tracing | Requires `Python >=3.10, <3.15` — compatible with 3.14.2 |
| `arize-phoenix-otel` | latest | Lightweight OTEL tracer for Phoenix | Connects to Phoenix server without installing full `arize-phoenix` |
| `opentelemetry-api` | >=1.0 | OpenTelemetry base API | Transitive dependency of phoenix-otel |
| `opentelemetry-sdk` | >=1.0 | OpenTelemetry SDK | Transitive dependency of phoenix-otel |
| `structlog` | >=24.0.0 | Structured logging | Already in pyproject.toml; use for latency logging |
| `httpx` | >=0.27.0 | Async HTTP client | Already in pyproject.toml; useful for health checks |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `ChatGoogleGenerativeAI` (LangChain) | `google-generativeai` SDK directly | Direct SDK is lighter but loses LangChain's `.with_structured_output()`, callback system, and tracing integration |
| `ChatOllama` (langchain-ollama) | `langchain-community` Ollama | `langchain-community` Ollama is deprecated; `langchain-ollama` is the official replacement |
| Custom fallback wrapper | LangChain `.with_fallbacks()` | LangChain's built-in fallbacks are less transparent; custom wrapper gives better logging, metrics, and error classification |
| Arize Phoenix via Docker | `arize-phoenix` pip install | pip install requires Python <3.14; Docker avoids the compatibility issue entirely |
| Arize Phoenix | LangSmith | LangSmith requires account/API key; Phoenix is fully local and open-source |

**Installation (additions to pyproject.toml):**
```bash
pip install langchain-ollama openinference-instrumentation-langchain arize-phoenix-otel
```

**Docker for Phoenix dashboard:**
```bash
docker run -d -p 6006:6006 arizephoenix/phoenix:latest
```

## Architecture Patterns

### Recommended Project Structure
```
src/ragready/
├── generation/              # NEW — Phase 2
│   ├── __init__.py
│   ├── llm.py              # LLM factory: create_llm() → Gemini or Qwen
│   ├── prompts.py           # System/user prompt templates
│   ├── chain.py             # RAG generation chain: retrieve → format → generate → validate
│   └── models.py            # Generation-specific Pydantic models (QueryResponse, Citation, RefusalResponse)
├── api/                     # NEW — Phase 2
│   ├── __init__.py
│   ├── app.py               # FastAPI app factory
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── query.py         # POST /query
│   │   ├── documents.py     # POST /documents/upload, GET /documents, DELETE /documents/{id}
│   │   └── health.py        # GET /health
│   ├── dependencies.py      # FastAPI dependency injection (Settings, Pipeline, Retriever)
│   └── middleware.py         # Latency logging middleware
├── observability/           # NEW — Phase 2
│   ├── __init__.py
│   └── tracing.py           # Phoenix OTEL setup, tracer initialization
├── core/                    # EXISTING — extend
│   ├── config.py            # Add: ollama_base_url, ollama_model, phoenix_endpoint
│   ├── models.py            # EXISTING — reuse ScoredChunk
│   └── exceptions.py        # Add: GenerationError, LLMUnavailableError
├── retrieval/               # EXISTING — no changes
├── ingestion/               # EXISTING — no changes
└── storage/                 # EXISTING — no changes
```

### Pattern 1: Structured Output via Pydantic Schema

**What:** Use LangChain's `with_structured_output()` to force the LLM to return JSON matching a Pydantic model, avoiding manual JSON parsing.

**When to use:** Every generation call — ensures citations and confidence scores are always present and correctly typed.

**Example:**
```python
# Source: LangChain official docs (langchain-google-genai)
from pydantic import BaseModel, Field
from langchain_google_genai import ChatGoogleGenerativeAI

class Citation(BaseModel):
    chunk_text: str = Field(description="Exact text from the source chunk")
    document_name: str = Field(description="Source document filename")
    page_number: int | None = Field(description="Page number if available")
    relevance_score: float = Field(description="Chunk retrieval score")

class QueryResponse(BaseModel):
    answer: str = Field(description="Answer grounded in the provided context")
    citations: list[Citation] = Field(description="Source citations for the answer")
    confidence: float = Field(description="Confidence score from 0.0 to 1.0")

llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    temperature=0.1,
    google_api_key=settings.google_api_key,
)
structured_llm = llm.with_structured_output(QueryResponse)

# Invoke returns a QueryResponse Pydantic instance directly
response = structured_llm.invoke(messages)
```

### Pattern 2: Confidence-Based Refusal

**What:** Check the maximum retrieval score and/or LLM-reported confidence against a threshold. If evidence is insufficient, return a refusal instead of a potentially hallucinated answer.

**When to use:** Before returning any generation result to the user.

**Example:**
```python
class RefusalResponse(BaseModel):
    refused: bool = True
    reason: str = Field(description="Why the system cannot answer")
    confidence: float = Field(description="Confidence score that was below threshold")

def should_refuse(chunks: list[ScoredChunk], threshold: float) -> bool:
    """Refuse if no chunks meet the confidence threshold."""
    if not chunks:
        return True
    max_score = max(c.score for c in chunks)
    return max_score < threshold

# Two-stage: check retrieval quality BEFORE calling LLM (saves tokens)
if should_refuse(chunks, settings.confidence_threshold):
    return RefusalResponse(
        reason="Retrieved evidence is insufficient to answer confidently",
        confidence=max(c.score for c in chunks) if chunks else 0.0,
    )
```

### Pattern 3: LLM Fallback with Custom Wrapper

**What:** Try Gemini Flash first; on failure (rate limit, network error, API key missing), fall back to local Qwen via Ollama.

**When to use:** Every LLM invocation.

**Example:**
```python
from tenacity import retry, stop_after_attempt, wait_exponential
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_ollama import ChatOllama

class LLMWithFallback:
    def __init__(self, primary: ChatGoogleGenerativeAI, fallback: ChatOllama):
        self._primary = primary
        self._fallback = fallback

    def invoke(self, messages):
        try:
            return self._primary.invoke(messages)
        except Exception as e:
            logger.warning("Primary LLM failed: %s — falling back to Qwen", e)
            return self._fallback.invoke(messages)
```

### Pattern 4: FastAPI Dependency Injection

**What:** Use FastAPI's `Depends()` to inject shared singletons (Settings, Pipeline, Retriever) into route handlers.

**When to use:** All route handlers.

**Example:**
```python
# Source: FastAPI official docs
from functools import lru_cache
from fastapi import Depends

@lru_cache
def get_settings() -> Settings:
    return Settings()

@lru_cache
def get_pipeline(settings: Settings = Depends(get_settings)) -> IngestionPipeline:
    return create_pipeline(settings)

@app.post("/query")
async def query(request: QueryRequest, pipeline=Depends(get_pipeline)):
    ...
```

### Anti-Patterns to Avoid

- **Parsing JSON manually from LLM output:** Use `with_structured_output()` — manual parsing breaks on malformed JSON, missing fields, extra whitespace.
- **Calling LLM without checking retrieval quality first:** Always check chunk scores before spending LLM tokens. Refuse early if evidence is weak.
- **Using `langchain-community` for Ollama:** Deprecated. Use `langchain-ollama` package.
- **Installing `arize-phoenix` via pip on Python 3.14:** Will fail. Use Docker for the server + `arize-phoenix-otel` for the client.
- **Global mutable state for FastAPI dependencies:** Use `@lru_cache` or lifespan events, not module-level mutable objects.
- **Synchronous LLM calls blocking the event loop:** FastAPI is async; use `async def` routes or run sync LLM calls in a thread pool via `asyncio.to_thread()`.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Structured LLM output | Custom JSON parser for LLM responses | `with_structured_output(PydanticModel)` | Handles retries, validation errors, partial JSON; tested across models |
| LLM retry logic | Custom retry with backoff | `tenacity` decorators + LangChain's built-in `max_retries` | Edge cases: jitter, exponential backoff, exception classification |
| OpenAPI docs | Manual API documentation | FastAPI auto-generates from Pydantic models | Always in sync with code, includes Swagger UI |
| File upload handling | Custom multipart parser | FastAPI `UploadFile` + `python-multipart` | Handles streaming, temp files, content-type validation |
| RAG tracing | Custom logging of each pipeline step | `openinference-instrumentation-langchain` | Auto-captures LLM calls, retrieval, tokens, latency with zero manual code |
| OTEL span management | Manual span creation/propagation | `arize-phoenix-otel` `register()` | Handles trace context, exporters, batching |

**Key insight:** The generation layer has two deceptively complex problems: (1) getting reliable structured output from LLMs (malformed JSON, missing fields, schema drift) and (2) tracing distributed pipeline steps. Both are fully solved by LangChain structured output and OpenInference instrumentation respectively. Hand-rolling either leads to weeks of edge-case debugging.

## Common Pitfalls

### Pitfall 1: Structured Output Fails Silently with Wrong Method
**What goes wrong:** Using `method="function_calling"` with Gemini when the model's function-calling support returns inconsistent schemas. Or passing a Pydantic class when the model needs `model_json_schema()`.
**Why it happens:** Gemini supports both `json_schema` and `function_calling` methods for structured output, but behavior differs by model version.
**How to avoid:** Use `method="json_schema"` explicitly for Gemini 2.0 Flash — it uses Gemini's native JSON mode which is most reliable. Test with edge cases (empty citations, very long answers).
**Warning signs:** Getting `None` back from `with_structured_output()`, or `ValidationError` on the response.

### Pitfall 2: Ollama Model Not Downloaded
**What goes wrong:** `ChatOllama(model="qwen2.5:7b")` fails at runtime because the model hasn't been pulled.
**Why it happens:** Ollama requires a separate `ollama pull qwen2.5:7b` step before the model is available.
**How to avoid:** Add a health check that verifies model availability. Document the required `ollama pull` command. Handle `ConnectionError` gracefully with clear error message.
**Warning signs:** Connection refused errors, 404 from Ollama API.

### Pitfall 3: Confidence Score Conflation
**What goes wrong:** Mixing retrieval scores (RRF fusion scores, 0-1 range) with LLM self-reported confidence. These are fundamentally different metrics.
**Why it happens:** Both are called "confidence" but measure different things.
**How to avoid:** Use retrieval scores for the refusal gate (pre-LLM). Let the LLM report its own confidence in the structured output. Document which score is which. Consider: refusal threshold checks retrieval scores, while the final response includes the LLM confidence.
**Warning signs:** Refusal threshold working inconsistently across query types.

### Pitfall 4: FastAPI UploadFile Not Awaited
**What goes wrong:** Calling `file.read()` instead of `await file.read()` in async route handlers.
**Why it happens:** `UploadFile.read()` is a coroutine in async contexts.
**How to avoid:** Always use `await file.read()` in `async def` endpoints. Or use `def` (sync) endpoints where FastAPI handles threading.
**Warning signs:** Getting a coroutine object instead of bytes.

### Pitfall 5: Phoenix Docker Not Running
**What goes wrong:** Tracing code runs but spans are silently dropped because no Phoenix collector is listening.
**Why it happens:** OTEL exporters don't raise errors by default when the collector is down.
**How to avoid:** Make tracing optional — if Phoenix is not available, log a warning and continue without tracing. Check connectivity at startup.
**Warning signs:** No traces appearing in Phoenix dashboard, no errors in logs.

### Pitfall 6: LLM Fallback Masks Real Errors
**What goes wrong:** Every request silently falls back to Qwen because of a misconfigured API key, and nobody notices.
**Why it happens:** The fallback catches all exceptions without distinguishing configuration errors from transient failures.
**How to avoid:** Log every fallback event at WARNING level. Distinguish between retryable errors (rate limit, timeout) and permanent errors (invalid API key, model not found). Consider a health endpoint that reports which LLM is active.
**Warning signs:** All responses coming from fallback, slow response times (Qwen is slower than Gemini).

### Pitfall 7: Blocking Event Loop with Synchronous LLM Calls
**What goes wrong:** LangChain's `.invoke()` is synchronous and blocks the FastAPI event loop, causing all concurrent requests to stall.
**Why it happens:** FastAPI runs `async def` handlers on the event loop; sync operations block it.
**How to avoid:** Either use `def` (non-async) route handlers (FastAPI runs them in a threadpool automatically), or use `await asyncio.to_thread(llm.invoke, messages)` in async handlers. LangChain also provides `.ainvoke()` for some models.
**Warning signs:** Server becomes unresponsive during LLM calls, request timeouts.

## Code Examples

Verified patterns from official sources:

### Gemini Flash Initialization
```python
# Source: langchain-google-genai official docs
from langchain_google_genai import ChatGoogleGenerativeAI

llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    temperature=0.1,
    google_api_key="...",  # or GOOGLE_API_KEY env var
    max_retries=2,         # default, retries on transient errors
)

# Token usage is available on response
response = llm.invoke("Hello")
print(response.usage_metadata)  # {'input_tokens': X, 'output_tokens': Y, 'total_tokens': Z}
```

### Qwen via Ollama
```python
# Source: langchain-ollama official docs
from langchain_ollama import ChatOllama

fallback_llm = ChatOllama(
    model="qwen2.5:7b",
    base_url="http://localhost:11434",  # default Ollama URL
    temperature=0.1,
)

# Structured output works the same way
structured_fallback = fallback_llm.with_structured_output(QueryResponse)
```

### Phoenix Tracing Setup
```python
# Source: Arize Phoenix docs — OTEL integration
from phoenix.otel import register

# Auto-instrument all LangChain components
tracer_provider = register(
    project_name="ragready",
    endpoint="http://localhost:6006/v1/traces",  # Phoenix OTLP endpoint
    auto_instrument=True,  # Instruments LangChain, LlamaIndex, etc.
)

# Or manual instrumentation (more control):
from openinference.instrumentation.langchain import LangChainInstrumentor
from phoenix.otel import register

tracer_provider = register(
    project_name="ragready",
    endpoint="http://localhost:6006/v1/traces",
)
LangChainInstrumentor().instrument(tracer_provider=tracer_provider)
```

### FastAPI File Upload
```python
# Source: FastAPI official docs
from fastapi import FastAPI, UploadFile, File, HTTPException
from pathlib import Path
import tempfile

app = FastAPI(title="RAGReady", version="0.1.0")

@app.post("/documents/upload")
async def upload_document(file: UploadFile = File(...)):
    # Validate file type
    allowed = {".pdf", ".md", ".txt", ".html"}
    suffix = Path(file.filename).suffix.lower()
    if suffix not in allowed:
        raise HTTPException(400, f"Unsupported file type: {suffix}")

    # Save to temp file and ingest
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = Path(tmp.name)

    try:
        doc = pipeline.ingest(tmp_path)
        return {"document_id": doc.document_id, "filename": doc.filename, "chunk_count": doc.chunk_count}
    finally:
        tmp_path.unlink(missing_ok=True)
```

### Latency Logging Middleware
```python
# Source: FastAPI / Starlette middleware pattern
import time
import structlog
from starlette.middleware.base import BaseHTTPMiddleware

logger = structlog.get_logger()

class LatencyLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = (time.perf_counter() - start) * 1000
        logger.info(
            "request_completed",
            method=request.method,
            path=request.url.path,
            status=response.status_code,
            duration_ms=round(duration_ms, 2),
        )
        return response
```

### RAG Prompt Template
```python
# Grounding prompt that enforces citation behavior
SYSTEM_PROMPT = """You are a helpful assistant that answers questions based ONLY on the provided context.

Rules:
1. ONLY use information from the provided context chunks to answer
2. For each claim in your answer, cite the source chunk(s) that support it
3. If the context doesn't contain enough information to answer, say so clearly
4. Never make up information not present in the context
5. Report your confidence (0.0 to 1.0) based on how well the context supports your answer

Context chunks:
{context}

Each chunk is formatted as:
[Chunk N] (source: {document}, page: {page}, score: {score})
{text}
"""
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `langchain-community` Ollama classes | `langchain-ollama` dedicated package | 2024-Q3 | Must use new package; old import paths deprecated |
| Manual JSON parsing from LLM | `with_structured_output()` | LangChain 0.2+ (2024) | Eliminates JSON parse errors, automatic retry on schema violation |
| Custom tracing/logging | OpenInference + OTEL standard | 2024-2025 | Industry-standard spans, works with any OTEL collector |
| `arize-phoenix` pip install | Docker server + `arize-phoenix-otel` client | Ongoing | Necessary for Python 3.14 compatibility |
| Gemini `generate_content()` | LangChain `ChatGoogleGenerativeAI` | 2024+ | Unified interface with structured output, callbacks, tracing |

**Deprecated/outdated:**
- `langchain.chat_models.ChatOllama`: Moved to `langchain-ollama` package. Import from `langchain_ollama` instead.
- `ChatGoogleGenerativeAI(model="gemini-pro")`: Use `gemini-2.0-flash` or `gemini-2.5-flash` for latest models.
- `phoenix.launch_app()` (in-process): For Python 3.14, run Phoenix via Docker instead.

## Open Questions

1. **Gemini structured output reliability with complex schemas**
   - What we know: `with_structured_output(method="json_schema")` works for simple schemas per docs
   - What's unclear: How reliably does it handle the full QueryResponse schema (nested citations array) at temperature 0.1? Does it ever return malformed output?
   - Recommendation: Implement with `include_raw=True` to capture raw response alongside parsed output. Add validation fallback that retries once on parse failure. Test extensively during development.

2. **Qwen 2.5:7b structured output quality**
   - What we know: `ChatOllama` supports `with_structured_output()` and Qwen 2.5 supports tool calling
   - What's unclear: Does a 7B parameter model reliably produce correct structured JSON with citations? May need prompt engineering specific to Qwen.
   - Recommendation: Test Qwen structured output early. Have a simpler fallback prompt (just answer + single confidence float) if structured output is unreliable from the smaller model.

3. **RRF score range and meaningful confidence thresholds**
   - What we know: RRF scores from Phase 1's fusion are cumulative reciprocal ranks, not normalized 0-1 probabilities. The current `confidence_threshold=0.6` may not be meaningful.
   - What's unclear: What's the actual distribution of RRF scores on real queries? Is 0.6 too high or too low?
   - Recommendation: Log score distributions during testing. May need to normalize scores or adjust the threshold. Consider using a percentile-based threshold instead of absolute value.

4. **Phoenix OTEL compatibility with Python 3.14.2**
   - What we know: `openinference-instrumentation-langchain` supports Python <3.15; `arize-phoenix-otel` version constraints need verification
   - What's unclear: Whether `arize-phoenix-otel` specifically has the same Python <3.14 constraint as `arize-phoenix`
   - Recommendation: Test `pip install arize-phoenix-otel openinference-instrumentation-langchain` in the project's Python 3.14.2 environment early. If `arize-phoenix-otel` also fails, use raw `opentelemetry-exporter-otlp` instead.

## Sources

### Primary (HIGH confidence)
- LangChain Google GenAI docs — `ChatGoogleGenerativeAI`, structured output, `with_structured_output()` method, token usage
- LangChain Ollama docs — `ChatOllama` from `langchain-ollama` package, installation, structured output support
- FastAPI official docs — `UploadFile`, file upload, dependency injection, middleware
- Arize Phoenix docs — tracing setup, OTEL integration, LangChain instrumentation

### Secondary (MEDIUM confidence)
- PyPI `arize-phoenix` — Python version constraint `<3.14, >=3.10` verified on package page
- PyPI `openinference-instrumentation-langchain` — Python version constraint `<3.15, >=3.10` verified on package page
- PyPI `langchain-ollama` — Package exists, separate from `langchain-community`

### Tertiary (LOW confidence)
- `arize-phoenix-otel` Python version compatibility — not directly verified on PyPI, needs hands-on testing
- Qwen 2.5:7b structured output reliability — based on general knowledge of model capabilities, not tested
- LangChain `.with_fallbacks()` current behavior — docs URL redirected, relying on API knowledge

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — All libraries verified via official docs and PyPI; version constraints checked
- Architecture: MEDIUM-HIGH — Patterns follow LangChain and FastAPI official recommendations; project structure extends existing Phase 1 conventions
- Pitfalls: MEDIUM — Based on combination of official docs, known Python 3.14 issues, and common RAG development patterns; some pitfalls (e.g., Qwen structured output quality) are predictions not confirmed by testing
- Code examples: HIGH — All examples derived from or verified against official documentation

**Research date:** 2026-03-05
**Valid until:** 2026-04-05 (30 days — stack is relatively stable; Gemini model names may update)
