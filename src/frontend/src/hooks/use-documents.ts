import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api, queryKeys } from '@/lib/api'

/**
 * TanStack hooks for document CRUD operations.
 * Fetches document list and provides upload/delete mutations with cache invalidation.
 */
export function useDocuments() {
  const queryClient = useQueryClient()

  const documentsQuery = useQuery({
    queryKey: queryKeys.documents,
    queryFn: () => api.getDocuments(),
  })

  const uploadMutation = useMutation({
    mutationFn: (file: File) => api.uploadDocument(file),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.documents })
      queryClient.invalidateQueries({ queryKey: queryKeys.health })
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (documentId: string) => api.deleteDocument(documentId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.documents })
      queryClient.invalidateQueries({ queryKey: queryKeys.health })
    },
  })

  return {
    documents: documentsQuery.data?.documents ?? [],
    count: documentsQuery.data?.count ?? 0,
    isLoading: documentsQuery.isLoading,
    upload: uploadMutation.mutate,
    uploadAsync: uploadMutation.mutateAsync,
    deleteDoc: deleteMutation.mutate,
    isUploading: uploadMutation.isPending,
    isDeleting: deleteMutation.isPending,
  }
}
