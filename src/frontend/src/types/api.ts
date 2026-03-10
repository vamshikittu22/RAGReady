/** Citation source from a retrieved document chunk */
export interface Citation {
  chunk_text: string
  document_name: string
  page_number: number | null
  relevance_score: number
}

/** Successful query response with grounded answer */
export interface QueryResponse {
  answer: string
  citations: Citation[]
  confidence: number
  refused: false
}

/** Refusal response when evidence is insufficient */
export interface RefusalResponse {
  refused: true
  reason: string
  confidence: number
  answer: ''
  citations: []
}

/** Union type for all query results */
export type QueryResult = QueryResponse | RefusalResponse

/** Response after uploading a document */
export interface UploadResponse {
  document_id: string
  filename: string
  file_type: string
  chunk_count: number
}

/** Metadata for a single indexed document */
export interface DocumentInfo {
  document_id: string
  filename: string
  file_type: string
  chunk_count: number
  created_at: string
}

/** Response from listing all documents */
export interface DocumentListResponse {
  documents: DocumentInfo[]
  count: number
}

/** Response after deleting a document */
export interface DeleteResponse {
  deleted: string
}

/** Backend health check response */
export interface HealthResponse {
  status: string
  version: string
  llm_model: string
  document_count: number
  phoenix_enabled: boolean
}

export interface DowntimeEntry {
  timestamp: string
  error: string
  message: string
}

/** Chat message for UI state (in-memory only) */
export interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
  citations?: Citation[]
  confidence?: number
  refused?: boolean
  refusalReason?: string
}

/** Evaluation results from the real pipeline */
export interface EvalResults {
  context_recall: number
  context_precision: number
  faithfulness: number
  answer_relevancy: number
  refusal_accuracy: number
  citation_accuracy: number
  hallucination_rate: number
  benchmark: {
    naive_recall: number
    hybrid_recall: number
    improvement: string
  }
  meta?: {
    total_questions: number
    in_context_questions: number
    out_of_context_questions: number
    answered: number
    refused: number
    duration_seconds: number
    timestamp: string
  }
  error?: string
}
