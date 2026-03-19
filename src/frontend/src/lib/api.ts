import type {
  QueryResult,
  DocumentListResponse,
  UploadResponse,
  DeleteResponse,
  HealthResponse,
} from '@/types/api'

export type {
  QueryResult,
  DocumentListResponse,
  UploadResponse,
  DeleteResponse,
  HealthResponse,
} from '@/types/api'

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

/** Custom error class for API responses */
export class ApiError extends Error {
  status: number

  constructor(status: number, message: string) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

/** Generic fetch wrapper with error handling */
async function fetchApi<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
    ...options,
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }))
    throw new ApiError(response.status, error.detail || 'Request failed')
  }

  return response.json()
}

/** TanStack Query key constants for cache consistency */
export const queryKeys = {
  documents: ['documents'] as const,
  health: ['health'] as const,
}

/** Streaming response types */
export type StreamToken = {
  type: 'token' | 'done' | 'refusal' | 'error'
  data: string | QueryResult | { reason: string; confidence: number } | string
}

/** Callback for processing streaming tokens */
type StreamCallback = (token: string, isDone: boolean, data?: QueryResult | { reason: string; confidence: number }) => void

/** Make a streaming request to /query/stream */
export async function queryStream(question: string, onToken: StreamCallback): Promise<QueryResult> {
  const response = await fetch(`${API_BASE}/query/stream`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ question }),
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }))
    throw new ApiError(response.status, error.detail || 'Request failed')
  }

  const reader = response.body?.getReader()
  if (!reader) {
    throw new ApiError(500, 'Response body is not readable')
  }

  const decoder = new TextDecoder()
  let buffer = ''
  let finalData: QueryResult | undefined

  while (true) {
    const { done, value } = await reader.read()
    if (done) break

    buffer += decoder.decode(value, { stream: true })
    const lines = buffer.split('\n')
    buffer = lines.pop() || ''

    for (const line of lines) {
      if (line.startsWith('data: ')) {
        try {
          const event: StreamToken = JSON.parse(line.slice(6))

          if (event.type === 'token') {
            onToken(event.data as string, false)
          } else if (event.type === 'done') {
            finalData = event.data as QueryResult
            onToken('', true, finalData)
          } else if (event.type === 'refusal') {
            const refusal = event.data as { reason: string; confidence: number }
            finalData = { ...refusal, refused: true, answer: '', citations: [] } as any
            onToken('', true, finalData)
          } else if (event.type === 'error') {
            throw new ApiError(500, event.data as string)
          }
        } catch (e) {
          console.error('Failed to parse SSE event:', e)
        }
      }
    }
  }

  return finalData as QueryResult
}

/** API client with methods for all backend endpoints */
export const api = {
  /** POST /query — ask a question, get cited answer */
  query: (question: string) =>
    fetchApi<QueryResult>('/query', {
      method: 'POST',
      body: JSON.stringify({ question }),
    }),

  /** GET /documents/ — list all indexed documents */
  getDocuments: () => fetchApi<DocumentListResponse>('/documents/'),

  /** POST /documents/upload — upload a document file */
  uploadDocument: async (file: File, customName?: string): Promise<UploadResponse> => {
    const formData = new FormData()
    formData.append('file', file)
    if (customName) {
      formData.append('custom_name', customName)
    }

    // Do NOT set Content-Type — browser sets multipart boundary automatically
    const response = await fetch(`${API_BASE}/documents/upload`, {
      method: 'POST',
      body: formData,
    })

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Upload failed' }))
      throw new ApiError(response.status, error.detail || 'Upload failed')
    }

    return response.json()
  },

  /** DELETE /documents/{id} — remove a document and its chunks */
  deleteDocument: (documentId: string) =>
    fetchApi<DeleteResponse>(`/documents/${documentId}`, {
      method: 'DELETE',
    }),

  /** GET /health — system health check */
  getHealth: () => fetchApi<HealthResponse>('/health'),

  /** GET /downtime-history — get records of llm failover attempts */
  getDowntimeHistory: () => fetchApi<import('@/types/api').DowntimeEntry[]>('/downtime-history'),

  /** GET /eval/results — get the latest evaluation results */
  getEvalResults: () => fetchApi<import('@/types/api').EvalResults>('/eval/results'),

  /** POST /eval/run — trigger a new evaluation run */
  runEvaluation: () =>
    fetchApi<{ status: string; message: string }>('/eval/run', { method: 'POST' }),
}
