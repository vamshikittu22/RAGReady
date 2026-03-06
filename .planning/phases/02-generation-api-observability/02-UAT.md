---
status: complete
phase: 02-generation-api-observability
source: [02-01-SUMMARY.md, 02-02-SUMMARY.md]
started: 2026-03-06T07:00:00Z
updated: 2026-03-06T08:30:00Z
---

## Tests

### 1. Server starts and Swagger UI loads
expected: Run `uvicorn ragready.api.app:create_app --factory --port 8000` from the project root (with venv active). Server starts without errors. Open http://localhost:8000/docs in browser. You should see the Swagger UI page titled "RAGReady" with 5 endpoint groups visible: POST /query, POST /documents/upload, GET /documents/, DELETE /documents/{document_id}, GET /health.
result: pass

### 2. Health endpoint returns system status
expected: In Swagger UI, expand GET /health, click "Try it out" then "Execute". Response should be 200 with JSON containing: status "healthy", version "0.1.0", llm_model "gemini-2.0-flash", fallback_model, document_count (number), phoenix_enabled false.
result: pass

### 3. Upload a document via API
expected: In Swagger UI, expand POST /documents/upload, click "Try it out". Upload any .txt or .md file. Response should be 200 with JSON containing: document_id (string), filename (original name), file_type (e.g. ".txt"), chunk_count (positive number).
result: pass

### 4. List ingested documents
expected: After uploading a document, expand GET /documents/ and execute. Response should show a JSON with "documents" array containing the document you just uploaded (with document_id, filename, file_type, chunk_count) and "count" of 1 (or however many you've uploaded).
result: pass

### 5. Delete a document
expected: Copy the document_id from the upload response. Expand DELETE /documents/{document_id}, paste the ID, and execute. Response should be 200 with {"deleted": "<your-doc-id>"}. Then GET /documents/ again — the deleted document should no longer appear.
result: pass

### 6. Upload rejects unsupported file type
expected: In POST /documents/upload, try uploading a file with an unsupported extension (e.g., .exe, .jpg, .csv). Response should be 400 with a detail message listing allowed types (.html, .md, .pdf, .txt).
result: pass — user tested with .docx, got 400 with allowed types listed

### 7. Query with no documents returns refusal
expected: With no documents ingested (or after deleting all), expand POST /query, enter any question like "What is RAG?". Response should be 200 with a refusal: {"refused": true, "reason": "...", "confidence": 0.0} — because there's no evidence to answer from.
result: pass — returned {"refused":true,"reason":"No relevant documents found to answer the question","confidence":0.0}

### 8. Query with ingested document returns cited answer
expected: Upload a .txt or .md document with some content. Then POST /query with a question about that content. Response should contain: "answer" (grounded in the document), "citations" array (each with chunk_text, document_name, page_number, relevance_score), and "confidence" (0.0-1.0). NOTE: Requires RAGREADY_GOOGLE_API_KEY set in environment or Ollama running locally.
result: pass — Ollama fallback (qwen2.5-coder:3b) returned grounded answer with citation, confidence 0.9

## Summary

total: 8
passed: 8
issues: 0
pending: 0
skipped: 0

## Gaps

### Gap 1: Gemini LLM factory crashed without API key (FIXED)
severity: critical
description: The create_llm() factory eagerly constructed ChatGoogleGenerativeAI, which threw a pydantic ValidationError if no RAGREADY_GOOGLE_API_KEY was set. This caused the entire /query endpoint to 500 — Ollama fallback never activated.
fix: Made Gemini construction lazy with _GeminiUnavailableStub. If no API key is set, the primary LLM is a stub that raises on invoke(), allowing the fallback to activate cleanly.
files: src/ragready/generation/llm.py

### Gap 2: Default ollama_model didn't match available model (FIXED)
severity: medium
description: Default ollama_model was "qwen2.5:7b" but user only had "qwen2.5-coder:3b" installed in Ollama.
fix: Changed default ollama_model in config.py to "qwen2.5-coder:3b".
files: src/ragready/core/config.py

### Gap 3: Confidence threshold incompatible with RRF scores (FIXED)
severity: critical
description: The pre-LLM refusal gate used a confidence_threshold of 0.6, but RRF fusion scores are in the range [0, ~0.033]. The threshold was impossible to reach, causing every query to be refused even with relevant documents.
fix: Lowered confidence_threshold default from 0.6 to 0.01 to be compatible with RRF score ranges. Updated tests accordingly.
files: src/ragready/core/config.py, tests/unit/test_generation_chain.py
