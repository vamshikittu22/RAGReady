# RAGReady — 2-Minute Demo Video Script

A concise walkthrough of RAGReady's core capabilities for portfolio review.

---

## Script

### 0:00–0:15 — Introduction

**[Screen: README hero section → Architecture diagram]**

> "RAGReady is a production-grade Retrieval-Augmented Generation system built with FastAPI and React. It features hybrid retrieval combining dense and sparse search, citation-enforced answers, and automated quality gates that run in CI."

**Action:** Scroll through the README to show the architecture diagram.

---

### 0:15–0:45 — Document Upload

**[Screen: Frontend → Documents tab]**

> "Let's start by uploading a document. RAGReady supports PDF, Markdown, plain text, and HTML."

**Action:**
1. Click the "Documents" tab
2. Click "Upload Document"
3. Select a sample PDF or Markdown file
4. Show the upload progress and success notification
5. Show the document appear in the list with metadata (filename, file type, chunk count)

> "The ingestion pipeline extracts text, chunks it with overlap, and indexes both dense embeddings in ChromaDB and sparse BM25 terms."

---

### 0:45–1:15 — Question Answering with Citations

**[Screen: Frontend → Chat tab]**

> "Now let's ask a question about the uploaded document."

**Action:**
1. Switch to the "Chat" tab
2. Type a question that the document can answer
3. Submit and show the answer appearing with a confidence score
4. Click to expand citations — show source chunks with document references

> "Every answer includes citations back to specific source chunks. The confidence score reflects how well the evidence supports the response."

---

### 1:15–1:30 — Refusal Demonstration

**[Screen: Frontend → Chat tab]**

> "What happens when we ask something outside the knowledge base?"

**Action:**
1. Type an unrelated question (e.g., about a topic not in any uploaded document)
2. Show the refusal response with explanation

> "RAGReady refuses to answer when evidence is insufficient — it doesn't hallucinate. This is enforced by the grounding gate in the generation chain."

---

### 1:30–1:50 — Evaluation Dashboard

**[Screen: Frontend → Dashboard tab]**

> "The evaluation dashboard shows automated quality metrics computed against a golden dataset of 51 question-answer pairs."

**Action:**
1. Switch to the "Dashboard" tab
2. Walk through the metric cards: faithfulness, relevancy, recall, precision
3. Point out the pass/fail indicators and target thresholds
4. Scroll to the benchmark comparison section

> "These metrics run in CI on every pull request. If any metric drops below its threshold, the merge is blocked. The benchmark section shows an 82% improvement in recall from hybrid retrieval over naive dense search."

---

### 1:50–2:00 — Closing

**[Screen: GitHub Actions → CI pipeline]**

> "RAGReady combines grounded generation, hybrid retrieval, and automated evaluation into a production-ready system. The full source is available on GitHub."

**Action:** Show the GitHub Actions CI page with passing checks.

---

## CI Screenshot Instructions

For a static portfolio or presentation, capture these screenshots:

1. **GitHub Actions overview** — Show the CI pipeline with all 4 jobs passing:
   - Lint & Type Check
   - Unit Tests
   - Integration Tests
   - Evaluation Quality Gates

2. **Evaluation job details** — Expand the evaluation job to show individual metric test results passing.

3. **Pull request checks** — Show a PR with the required status checks passing, demonstrating the quality gate enforcement.

**Screenshot locations:** Save to `docs/screenshots/` for use in presentations.

---

## Recording Tips

- Use a screen recording tool (OBS, Loom, or QuickTime)
- Resolution: 1920×1080 or higher
- Show the browser in full-screen mode
- Use a dark theme for better contrast in recordings
- Pre-upload a document so the demo flows smoothly without waiting for processing
- Keep narration concise — the 2-minute format works best for portfolio review
