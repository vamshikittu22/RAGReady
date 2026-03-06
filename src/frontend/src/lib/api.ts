import type {
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
  uploadDocument: async (file: File): Promise<UploadResponse> => {
    const formData = new FormData()
    formData.append('file', file)

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
}
