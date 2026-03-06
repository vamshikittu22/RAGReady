# Phase 3 Research: Evaluation & CI/CD Quality Gates

**Phase:** 3 of 4
**Researched:** 2026-03-06
**Overall Confidence:** MEDIUM-HIGH
**Critical Constraint:** No Google API key. System runs on Ollama (qwen2.5-coder:3b) only. LLM-as-judge with a 3B model is a major reliability risk.

---

## Executive Summary

Phase 3 must deliver two capabilities: (1) an automated evaluation pipeline that measures RAG quality across 7 metrics, and (2) GitHub Actions CI/CD that blocks PRs when quality degrades. The fundamental challenge is that most RAG evaluation frameworks (Ragas, DeepEval) assume access to a powerful LLM judge (GPT-4, Claude, Gemini), but this project has only a 3B parameter local model available. This research identifies a **hybrid evaluation strategy** that combines non-LLM metrics (deterministic checks, HHEM classifier) with cautious use of Ollama for LLM-dependent metrics.

### Key Findings

1. **DeepEval has built-in Ollama support** (`deepeval set-ollama --model=<name>`) and also supports custom LLM wrappers via `DeepEvalBaseLLM` — but warns that small models may produce unreliable evaluations.
2. **Ragas 0.4.x supports Ollama** through its OpenAI-compatible API adapter (`OpenAI(base_url="http://localhost:11434/v1")`), and offers `FaithfulnesswithHHEM` — a classifier-based Faithfulness metric that requires NO LLM judge (uses Vectara's HHEM-2.1-Open T5 model instead).
3. **Custom metrics (Refusal Accuracy, Citation Accuracy) should be deterministic** — compare pipeline output against golden dataset expected behavior without involving any LLM.
4. **GitHub Actions with Ollama is complex** — requires installing Ollama, pulling a model (1-2GB download), and starting the server in CI. Alternative: run only deterministic/non-LLM metrics in CI, run full eval locally.
5. **Ragas 0.4.x has breaking API changes** — uses `llm_factory()` with adapter pattern, collection-based metric imports (`from ragas.metrics.collections import Faithfulness`). Legacy imports are deprecated.

---

## Requirement-by-Requirement Analysis

### EVAL-01: Golden Dataset (50+ Q&A pairs)

**What's needed:** A JSON file with 50+ entries, each containing:
- `question`: The user query
- `expected_answer`: The ground-truth answer (for Answer Relevancy)
- `expected_contexts`: List of expected source chunks (for Context Recall)
- `should_refuse`: Boolean flag for out-of-domain questions (for Refusal Accuracy)
- `expected_citations`: Expected document sources (for Citation Accuracy)

**Challenge:** We don't know what documents are ingested. `data/raw/` doesn't exist (gitignored). The golden dataset must be **created alongside test documents** — a small corpus of known documents that get ingested for evaluation.

**Approach:**
1. Create 3-5 small test documents (Markdown/TXT) in `tests/evaluation/fixtures/` covering a specific domain
2. Build golden dataset entries against those documents
3. Include 10-15 adversarial/out-of-domain questions (should_refuse=True)
4. Total: ~35-40 answerable + ~10-15 refusal = 50+ pairs
5. Store as `tests/evaluation/golden_dataset.json`

**Schema:**
```json
{
  "version": "1.0",
  "documents": ["doc1.md", "doc2.txt"],
  "entries": [
    {
      "id": "q001",
      "question": "What is X?",
      "expected_answer": "X is ...",
      "expected_contexts": ["chunk text snippet 1"],
      "expected_documents": ["doc1.md"],
      "should_refuse": false,
      "category": "factual"
    }
  ]
}
```

**Confidence:** HIGH — standard practice, no external dependencies.

---

### EVAL-02: Faithfulness (target >0.85)

**What it measures:** Whether the generated answer is factually grounded in the retrieved context (no hallucination).

**Options:**
| Approach | LLM Required? | Reliability with 3B model | Recommendation |
|----------|---------------|--------------------------|----------------|
| Ragas `Faithfulness` | YES (LLM judge) | LOW — 3B model struggles with claim decomposition | Not recommended as primary |
| Ragas `FaithfulnesswithHHEM` | NO — uses Vectara HHEM-2.1-Open (T5 classifier) | HIGH — classifier-based, deterministic | **PRIMARY choice** |
| DeepEval `FaithfulnessMetric` | YES (LLM judge) | LOW-MEDIUM — DeepEval warns about custom models | Secondary/optional |

**Recommendation:** Use **Ragas `FaithfulnesswithHHEM`** as the primary Faithfulness metric. It uses Vectara's HHEM-2.1-Open model (a T5-based classifier fine-tuned on hallucination detection) instead of an LLM judge. This completely bypasses the 3B model limitation.

**How HHEM works:**
- Downloads a ~300MB T5 classifier model from HuggingFace
- Classifies each (claim, context) pair as "hallucination" or "faithful"
- No prompt engineering or JSON parsing required — pure classification
- Deterministic output (same input → same score)

**Ragas 0.4.x API:**
```python
from ragas.metrics import FaithfulnesswithHHEM
metric = FaithfulnesswithHHEM()
# Uses HHEM-2.1-Open model internally — no LLM factory needed
```

**Confidence:** MEDIUM — HHEM API verified in Ragas docs, but exact 0.4.x import path needs validation during implementation. The HHEM model itself is well-established.

---

### EVAL-03: Answer Relevancy (target >0.80)

**What it measures:** Whether the answer is relevant to the question asked (regardless of factual correctness).

**Options:**
| Approach | LLM Required? | Reliability with 3B model |
|----------|---------------|--------------------------|
| Ragas `ResponseRelevancy` | YES — generates hypothetical questions from answer, embeds & compares | MEDIUM — embedding comparison is robust, question generation is the weak link |
| DeepEval `AnswerRelevancyMetric` | YES — LLM judge rates relevance | LOW-MEDIUM |
| Custom: Embedding similarity | NO — embed question + answer, compute cosine similarity | HIGH — fully deterministic |

**Recommendation:** **Dual approach:**
1. **Primary:** Custom embedding-based relevancy — embed the question and the answer using all-MiniLM-L6-v2, compute cosine similarity. Simple, deterministic, no LLM needed.
2. **Secondary (optional):** Ragas `ResponseRelevancy` via Ollama — useful for comparison but less reliable with 3B model.

The custom embedding approach won't capture semantic nuances as well as LLM-based evaluation, but it's reliable and consistent. A cosine similarity of 0.80+ between question embedding and answer embedding is a reasonable proxy for relevancy.

**Confidence:** MEDIUM — custom approach is sound but less validated than standard metrics. Ragas approach depends on Ollama model quality.

---

### EVAL-04: Context Recall (target >0.75)

**What it measures:** Whether the retrieved contexts contain the information needed to answer the question (compared against ground-truth expected contexts).

**Options:**
| Approach | LLM Required? | Reliability |
|----------|---------------|-------------|
| Ragas `ContextRecall` | YES — LLM classifies each ground-truth sentence as found/not-found in contexts | LOW with 3B |
| Custom: Token overlap | NO — compute token/word overlap between expected_contexts and retrieved chunks | HIGH — deterministic |
| Custom: Embedding recall | NO — embed expected_contexts and retrieved chunks, check coverage via similarity threshold | HIGH — deterministic |

**Recommendation:** **Custom embedding-based Context Recall:**
1. Embed each `expected_context` from golden dataset
2. Embed each retrieved chunk
3. For each expected context, check if any retrieved chunk has cosine similarity > threshold (0.7)
4. Context Recall = (matched expected contexts) / (total expected contexts)

This is essentially what Ragas does, but without the LLM judge step. It measures retrieval coverage directly.

**Confidence:** MEDIUM — custom metric is defensible but not a standard Ragas metric. Must be clearly documented as "embedding-based Context Recall" in reports.

---

### EVAL-05: Context Precision (target >0.70)

**What it measures:** Whether retrieved contexts are relevant (not noise). A high Context Precision means the retriever isn't returning irrelevant chunks.

**Options:**
| Approach | LLM Required? | Reliability |
|----------|---------------|-------------|
| Ragas `ContextPrecision` | YES — LLM judges each context's relevance | LOW with 3B |
| Custom: Embedding precision | NO — check each retrieved chunk against question embedding | HIGH |

**Recommendation:** **Custom embedding-based Context Precision:**
1. Embed the question
2. Embed each retrieved chunk
3. A chunk is "relevant" if cosine similarity with question > threshold (0.5)
4. Context Precision = (relevant chunks) / (total retrieved chunks)

This measures whether the retriever is returning semantically related chunks. Lower threshold than Context Recall because we're checking "general relevance" not "exact match."

**Confidence:** MEDIUM — same caveat as Context Recall. Must document clearly.

---

### EVAL-06: Refusal Accuracy (target >90%)

**What it measures:** Does the system correctly refuse to answer when evidence is insufficient?

**Implementation:** **Fully deterministic — no LLM judge needed.**

```python
def refusal_accuracy(results: list[dict], golden: list[dict]) -> float:
    correct = 0
    total = 0
    for entry, result in zip(golden, results):
        if entry["should_refuse"]:
            total += 1
            if isinstance(result, RefusalResponse) or result.get("refused"):
                correct += 1
        else:
            total += 1
            if not (isinstance(result, RefusalResponse) or result.get("refused")):
                correct += 1
    return correct / total if total else 0.0
```

This checks:
- Questions marked `should_refuse=True`: Did the system return `RefusalResponse`?
- Questions marked `should_refuse=False`: Did the system return `QueryResponse`?

**Confidence:** HIGH — purely deterministic, checks system behavior against golden labels.

---

### EVAL-07: Citation Accuracy (target >95%)

**What it measures:** Do the citations in the response actually correspond to chunks that were retrieved?

**Implementation:** **Fully deterministic — no LLM judge needed.**

```python
def citation_accuracy(results: list[QueryResponse], golden: list[dict]) -> float:
    correct_citations = 0
    total_citations = 0
    for result in results:
        if hasattr(result, 'citations'):
            for citation in result.citations:
                total_citations += 1
                # Check: does this citation reference a real document?
                if citation.document_name in known_documents:
                    correct_citations += 1
    return correct_citations / total_citations if total_citations else 1.0
```

Additional checks:
1. Every citation's `document_name` exists in the ingested documents
2. Every citation's `chunk_text` appears (substring match) in the retrieved chunks
3. Every citation's `page_number` is valid for that document

**Confidence:** HIGH — purely deterministic, validates citation integrity against known data.

---

### EVAL-08: Naive vs Hybrid Benchmark

**What it measures:** Side-by-side comparison proving hybrid retrieval (dense + sparse + RRF) outperforms naive dense-only retrieval.

**Implementation:**
1. Run golden dataset through `DenseRetriever` only (already exists separately)
2. Run golden dataset through `HybridRetriever` (dense + sparse + RRF)
3. Compare all metrics side-by-side
4. Generate a comparison report (JSON + human-readable)

**Code architecture:**
```python
# Both retrievers are independently constructable
from ragready.retrieval.dense import DenseRetriever
from ragready.retrieval.hybrid import HybridRetriever, create_retriever

# Run same golden dataset through both, collect metrics
naive_results = evaluate_pipeline(retriever=dense_only, dataset=golden)
hybrid_results = evaluate_pipeline(retriever=hybrid, dataset=golden)
comparison = build_comparison_report(naive_results, hybrid_results)
```

**Confidence:** HIGH — both `DenseRetriever` and `HybridRetriever` already exist with independent constructors.

---

### EVAL-09: Hallucination Rate (target <5%)

**What it measures:** Percentage of responses containing fabricated information not grounded in retrieved context.

**Implementation:** Derived from Faithfulness metric:
```
Hallucination Rate = 1 - Faithfulness Score
```

If HHEM-based Faithfulness = 0.95, then Hallucination Rate = 0.05 (5%).

No separate metric needed — this is the inverse of Faithfulness.

**Confidence:** HIGH — standard derivation.

---

### CI-01: GitHub Actions on Every PR

**Challenge:** Running evaluation in CI requires either:
1. **Ollama in CI** — install Ollama, pull model (1-2GB), start server. Adds 2-5 min to CI setup and requires significant runner resources.
2. **Deterministic-only CI** — run only metrics that don't need an LLM (Refusal Accuracy, Citation Accuracy, embedding-based metrics). Run full eval locally.

**Recommendation: Option 2 — Deterministic metrics in CI, full eval on-demand.**

**Rationale:**
- HHEM model download is ~300MB — acceptable for CI with caching
- Embedding model (all-MiniLM-L6-v2) is ~80MB — acceptable with caching
- Ollama + qwen2.5-coder:3b is ~2GB — too heavy for every PR, and unreliable results anyway
- Deterministic metrics catch real regressions (broken citations, broken refusal logic)
- LLM-dependent metrics run via `make eval-full` locally or in a scheduled workflow

**CI Workflow structure:**
```yaml
# .github/workflows/ci.yml
jobs:
  lint-type-check:
    - ruff check
    - mypy

  unit-tests:
    - pytest tests/unit/

  integration-tests:
    - pytest tests/integration/

  evaluation:
    - Ingest test documents
    - Run deterministic eval metrics (Refusal Accuracy, Citation Accuracy, HHEM Faithfulness)
    - Assert thresholds
    - Save report as artifact
```

**Confidence:** MEDIUM — GitHub Actions structure is standard, but CI with HHEM model download needs caching validation.

---

### CI-02: PR Blocking on Metric Regression

**Implementation:**
- Use `pytest` with assertions on metric thresholds
- Failing assertion = failing test = blocked PR (with branch protection rules)
- DeepEval's `@deepeval.test` decorator or `assert_test()` can assert thresholds natively

```python
# tests/evaluation/test_quality_gates.py
def test_faithfulness_threshold(eval_results):
    assert eval_results["faithfulness"] >= 0.85, (
        f"Faithfulness {eval_results['faithfulness']:.2f} below threshold 0.85"
    )
```

**Branch protection:** Require the `evaluation` job to pass before merge.

**Confidence:** HIGH — standard pytest + GitHub branch protection.

---

### CI-03: Evaluation Reports as Artifacts

**Implementation:**
```yaml
- uses: actions/upload-artifact@v4
  with:
    name: evaluation-report
    path: reports/evaluation-*.json
```

Generate a JSON + Markdown report per evaluation run with:
- All metric scores
- Pass/fail status per metric
- Comparison with thresholds
- Timestamp

**Confidence:** HIGH — standard GitHub Actions pattern.

---

### CI-04: Linting and Type Checking in CI

**Implementation:** Already have `ruff` and `mypy` in dev dependencies.

```yaml
- name: Lint
  run: ruff check src/ tests/

- name: Type check
  run: mypy src/
```

**Confidence:** HIGH — tools already configured in pyproject.toml.

---

## Technology Decision: DeepEval vs Ragas vs Custom

### Verdict: Hybrid — Ragas HHEM + Custom Deterministic + DeepEval for CI integration

| Metric | Implementation | Framework | LLM Needed? |
|--------|---------------|-----------|-------------|
| Faithfulness (EVAL-02) | HHEM classifier | Ragas `FaithfulnesswithHHEM` | NO |
| Answer Relevancy (EVAL-03) | Embedding cosine similarity | Custom | NO |
| Context Recall (EVAL-04) | Embedding coverage check | Custom | NO |
| Context Precision (EVAL-05) | Embedding relevance check | Custom | NO |
| Refusal Accuracy (EVAL-06) | Deterministic label comparison | Custom | NO |
| Citation Accuracy (EVAL-07) | Deterministic validation | Custom | NO |
| Hallucination Rate (EVAL-09) | 1 - Faithfulness | Derived | NO |
| Naive vs Hybrid (EVAL-08) | Side-by-side benchmark | Custom script | NO |

**Key insight:** With this approach, **zero metrics require an LLM judge**. This completely sidesteps the 3B model reliability problem.

**Trade-off:** Embedding-based Answer Relevancy and Context Recall are less nuanced than LLM-judged versions. They may miss subtle semantic mismatches that a GPT-4 judge would catch. However, they are:
1. **Deterministic** — same input → same score
2. **Fast** — no LLM inference latency
3. **Reliable in CI** — no Ollama server needed, no model download, no JSON parsing failures
4. **Sufficient for a portfolio project** — demonstrates evaluation methodology and quality gates

**If user later gets a Google API key**, we can add Ragas LLM-based metrics alongside custom ones for richer evaluation.

---

## Ragas 0.4.x API Guide (Critical)

### Breaking Changes from Tutorials

Most tutorials use Ragas 0.2.x patterns. Here's what changed in 0.4.x:

| Old (0.2.x) | New (0.4.x) | Notes |
|-------------|-------------|-------|
| `from ragas.metrics import faithfulness` | `from ragas.metrics import Faithfulness` | Capitalized class names |
| `from ragas.metrics import faithfulness` | `from ragas.metrics.collections import Faithfulness` | New collections module (preferred) |
| `evaluate(dataset, metrics=[faithfulness])` | Changed signature, uses `EvaluationDataset` | Check 0.4.x docs |
| `RagasLLM` wrapper | `llm_factory("model", provider="openai", client=client)` | Adapter pattern |
| Direct LLM assignment | `llm_factory()` with `InstructorAdapter` or `LiteLLMAdapter` | Must use factory |

### Ollama with Ragas 0.4.x

```python
from openai import OpenAI
from ragas.llms import llm_factory

# Point OpenAI client at Ollama's compatible API
client = OpenAI(
    api_key="ollama",  # Ollama doesn't check this
    base_url="http://localhost:11434/v1",
)

llm = llm_factory(
    "qwen2.5-coder:3b",
    provider="openai",
    client=client,
)
```

**Confidence:** MEDIUM — verified from Ragas docs, but exact 0.4.x behavior with Ollama needs hands-on testing.

---

## DeepEval with Ollama

### Built-in Ollama Support

```bash
# CLI configuration
deepeval set-ollama --model=qwen2.5-coder:3b
```

### Custom LLM Wrapper (More Control)

```python
from deepeval.models import DeepEvalBaseLLM

class OllamaLLM(DeepEvalBaseLLM):
    def __init__(self, model_name: str = "qwen2.5-coder:3b"):
        self.model_name = model_name

    def load_model(self):
        return self.model_name

    def generate(self, prompt: str) -> str:
        # Call Ollama API
        ...

    async def a_generate(self, prompt: str) -> str:
        # Async call to Ollama
        ...

    def get_model_name(self) -> str:
        return self.model_name
```

### DeepEval Warning

> "We CANNOT guarantee evaluations will work as expected when using a custom model"

Small models (3B) may:
- Fail to produce valid JSON for metric computation
- Give inconsistent scores across runs
- Miss subtle hallucinations or relevancy issues

**DeepEval CI Integration:**
```bash
# Run evaluation tests
deepeval test run tests/evaluation/

# Flags:
# -i: Ignore errors (continue on metric failures)
# -c: Use cache (skip unchanged test cases)
```

Native pytest integration: `conftest.py` picks up DeepEval fixtures automatically.

**Confidence:** MEDIUM — Ollama support verified in DeepEval docs, but 3B model reliability is a known concern.

---

## Project Structure for Phase 3

```
tests/
  evaluation/
    __init__.py
    conftest.py                 # Fixtures: test documents, ingestion, retrievers
    golden_dataset.json         # 50+ Q&A pairs
    fixtures/
      doc1_python_basics.md     # Test document 1
      doc2_web_development.md   # Test document 2
      doc3_data_structures.md   # Test document 3
    metrics/
      __init__.py
      faithfulness.py           # HHEM-based faithfulness
      relevancy.py              # Embedding-based answer relevancy
      context_recall.py         # Embedding-based context recall
      context_precision.py      # Embedding-based context precision
      refusal_accuracy.py       # Deterministic refusal check
      citation_accuracy.py      # Deterministic citation validation
    test_quality_gates.py       # pytest assertions on thresholds
    test_benchmark.py           # Naive vs hybrid comparison

scripts/
  evaluate.py                   # CLI: run full evaluation
  benchmark.py                  # CLI: run naive vs hybrid comparison
  generate_report.py            # Generate HTML/JSON evaluation report

reports/                        # Generated eval reports (gitignored)
  evaluation-YYYY-MM-DD.json
  benchmark-YYYY-MM-DD.json

.github/
  workflows/
    ci.yml                      # Main CI: lint + type check + tests + eval
```

---

## Dependencies to Add

```toml
# In pyproject.toml [project.optional-dependencies]
eval = [
    "ragas>=0.4.0",                # For FaithfulnesswithHHEM
    "deepeval>=3.8.0",             # For CI test integration (optional)
    "scikit-learn>=1.5.0",         # For cosine similarity in custom metrics
]
```

**Note:** `sentence-transformers` is already a dependency — used for embedding-based custom metrics (Answer Relevancy, Context Recall, Context Precision).

`scikit-learn` might not be needed if we use `numpy` directly for cosine similarity (already a dependency). `numpy.dot(a, b) / (numpy.linalg.norm(a) * numpy.linalg.norm(b))` is sufficient.

**Revised: No new dependencies needed for custom metrics.** `numpy` and `sentence-transformers` are already installed. Only `ragas>=0.4.0` is needed for HHEM Faithfulness.

---

## Plan Structure Recommendation

### Plan 03-01: Golden Dataset + Evaluation Pipeline

**Scope:** EVAL-01 through EVAL-09

**Tasks:**
1. Create test document fixtures (3-5 small Markdown/TXT documents)
2. Build golden dataset JSON (50+ Q&A pairs including adversarial)
3. Implement custom metrics module (`tests/evaluation/metrics/`)
   - Embedding-based: Answer Relevancy, Context Recall, Context Precision
   - Deterministic: Refusal Accuracy, Citation Accuracy
   - Derived: Hallucination Rate = 1 - Faithfulness
4. Integrate Ragas `FaithfulnesswithHHEM` for Faithfulness metric
5. Build evaluation runner (`scripts/evaluate.py`)
6. Build benchmark runner (`scripts/benchmark.py`) — Naive vs Hybrid comparison
7. Write pytest quality gate tests (`tests/evaluation/test_quality_gates.py`)
8. Generate evaluation reports (JSON format)

**Estimated complexity:** HIGH — most code in the phase, many metrics to implement and validate.

### Plan 03-02: CI/CD Quality Gates

**Scope:** CI-01 through CI-04

**Tasks:**
1. Create `.github/workflows/ci.yml`
2. Configure lint + type check jobs (ruff, mypy)
3. Configure unit + integration test jobs
4. Configure evaluation job (deterministic metrics + HHEM)
5. Set up HuggingFace model caching in CI (HHEM + embedding models)
6. Configure artifact upload for evaluation reports
7. Document branch protection rules for PR blocking

**Estimated complexity:** MEDIUM — mostly configuration, but CI caching needs careful setup.

---

## Risk Assessment

| Risk | Severity | Likelihood | Mitigation |
|------|----------|-----------|------------|
| HHEM model not available in Ragas 0.4.x exact API | HIGH | MEDIUM | Verify import path first; fallback to custom HHEM integration via `transformers` |
| Embedding-based metrics produce meaningless scores | MEDIUM | LOW | Validate against 10 hand-labeled examples before using at scale |
| CI model download takes too long | MEDIUM | MEDIUM | Cache HuggingFace models in GitHub Actions cache |
| Golden dataset doesn't match realistic use cases | MEDIUM | LOW | Include diverse question types: factual, comparative, out-of-domain |
| Ragas 0.4.x has additional breaking changes not documented | MEDIUM | MEDIUM | Pin exact version, test in isolation first |
| qwen2.5-coder:3b is needed for pipeline execution (not just eval) | HIGH | HIGH | Pipeline runs on Ollama for answers — test documents must work with 3B model quality |

---

## Open Questions for Implementation

1. **HHEM Import Path:** Is it `from ragas.metrics import FaithfulnesswithHHEM` or a different path in 0.4.x? Need to verify during implementation.
2. **Test Document Domain:** What domain should test documents cover? Technical topics (Python, web dev) are likely best since qwen2.5-coder:3b is a coding model.
3. **Embedding Similarity Thresholds:** What cosine similarity thresholds work well for Answer Relevancy (0.5? 0.6? 0.7?)? Need empirical calibration with golden dataset.
4. **CI Runner Resources:** Do GitHub Actions free-tier runners (2-core, 7GB RAM) have enough memory for HHEM model + embedding model simultaneously?
5. **HHEM Model Size:** Is HHEM-2.1-Open ~300MB? Need to verify for CI caching strategy.

---

## Sources

| Source | Type | Confidence |
|--------|------|------------|
| DeepEval docs — Using Ollama section | Official docs | HIGH |
| DeepEval docs — Metrics Introduction | Official docs | HIGH |
| DeepEval docs — Custom LLMs guide (`DeepEvalBaseLLM`) | Official docs | HIGH |
| DeepEval docs — Faithfulness metric | Official docs | HIGH |
| Ragas docs — LLM Factory & Custom Models | Official docs | MEDIUM (0.4.x API may differ) |
| Ragas docs — `FaithfulnesswithHHEM` metric | Official docs | MEDIUM |
| Ragas docs — Faithfulness metric (claim decomposition) | Official docs | HIGH |
| Project source code — `chain.py`, `models.py`, `dense.py`, `hybrid.py`, `config.py`, `llm.py` | Codebase | HIGH |
| Project planning — `ROADMAP.md`, `REQUIREMENTS.md`, `STACK.md`, `PITFALLS.md` | Codebase | HIGH |
| Training data (Claude) — evaluation patterns, CI/CD practices | Training | LOW-MEDIUM |
