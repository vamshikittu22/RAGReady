import { useMutation, useState, useCallback } from '@tanstack/react-query'
import { api, queryStream, QueryResult } from '@/lib/api'

/**
 * TanStack mutation hook for RAG queries.
 * Uses useMutation because /query is a user-initiated action, not idempotent data fetching.
 */
export function useQueryRag() {
  const mutation = useMutation({
    mutationFn: (question: string) => api.query(question),
  })

  return {
    ask: mutation.mutate,
    askAsync: mutation.mutateAsync,
    data: mutation.data,
    isPending: mutation.isPending,
    isError: mutation.isError,
    error: mutation.error,
    reset: mutation.reset,
  }
}

/**
 * Hook for streaming RAG queries with real-time token updates.
 * Returns the accumulated answer and a function to execute the query.
 */
export function useQueryRagStream() {
  const [streamedAnswer, setStreamedAnswer] = useState('')
  const [isStreaming, setIsStreaming] = useState(false)
  const [streamError, setStreamError] = useState<Error | null>(null)

  const executeStream = useCallback(async (question: string): Promise<QueryResult | null> => {
    setStreamedAnswer('')
    setIsStreaming(true)
    setStreamError(null)

    try {
      const result = await queryStream(question, (token, isDone) => {
        if (!isDone && typeof token === 'string') {
          setStreamedAnswer(prev => prev + token)
        }
      })
      return result
    } catch (err) {
      setStreamError(err instanceof Error ? err : new Error(String(err)))
      return null
    } finally {
      setIsStreaming(false)
    }
  }, [])

  return {
    streamedAnswer,
    isStreaming,
    streamError,
    executeStream,
    clearStream: () => {
      setStreamedAnswer('')
      setStreamError(null)
    },
  }
}
