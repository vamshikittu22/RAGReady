import { useMutation } from '@tanstack/react-query'
import { api } from '@/lib/api'

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
