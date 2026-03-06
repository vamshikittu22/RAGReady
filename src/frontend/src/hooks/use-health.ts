import { useQuery } from '@tanstack/react-query'
import { api, queryKeys } from '@/lib/api'

/**
 * TanStack query hook for backend health status.
 * Polls every 30 seconds to keep the health indicator current.
 */
export function useHealth() {
  const healthQuery = useQuery({
    queryKey: queryKeys.health,
    queryFn: () => api.getHealth(),
    refetchInterval: 30_000,
  })

  return {
    health: healthQuery.data,
    isHealthy: healthQuery.isSuccess,
    isLoading: healthQuery.isLoading,
  }
}
