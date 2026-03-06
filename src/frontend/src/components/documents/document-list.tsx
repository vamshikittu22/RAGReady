import { useState } from 'react'
import type { DocumentInfo } from '@/types/api'
import { useDocuments } from '@/hooks/use-documents'
import { DocumentCard } from '@/components/documents/document-card'
import { UploadDialog } from '@/components/documents/upload-dialog'
import { Skeleton } from '@/components/ui/skeleton'
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog'
import { toast } from 'sonner'
import { FileText } from 'lucide-react'

export function DocumentList() {
  const { documents, count, isLoading, deleteDoc, isDeleting } = useDocuments()
  const [deleteTarget, setDeleteTarget] = useState<DocumentInfo | null>(null)

  function handleDeleteConfirm() {
    if (!deleteTarget) return
    deleteDoc(deleteTarget.document_id, {
      onSuccess: () => {
        toast.success('Document deleted')
        setDeleteTarget(null)
      },
      onError: (err: Error) => {
        toast.error(err.message || 'Failed to delete document')
      },
    })
  }

  function handleDeleteRequest(documentId: string) {
    const doc = documents.find((d) => d.document_id === documentId)
    if (doc) setDeleteTarget(doc)
  }

  if (isLoading) {
    return (
      <div>
        <div className="mb-4 flex items-center justify-between">
          <Skeleton className="h-5 w-32" />
          <Skeleton className="h-8 w-40" />
        </div>
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 3 }).map((_, i) => (
            <Skeleton key={i} className="h-32 rounded-xl" />
          ))}
        </div>
      </div>
    )
  }

  return (
    <div>
      <div className="mb-4 flex items-center justify-between">
        <p className="text-sm text-muted-foreground">
          {count} document{count !== 1 ? 's' : ''}
        </p>
        <UploadDialog />
      </div>

      {documents.length === 0 ? (
        <div className="flex flex-col items-center justify-center gap-3 rounded-lg border border-dashed py-16 text-center">
          <FileText className="h-10 w-10 text-muted-foreground/50" />
          <div>
            <p className="font-medium text-muted-foreground">No documents uploaded yet</p>
            <p className="text-sm text-muted-foreground/70">
              Upload your first document to get started.
            </p>
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
          {documents.map((doc) => (
            <DocumentCard
              key={doc.document_id}
              document={doc}
              onDelete={handleDeleteRequest}
              isDeleting={isDeleting}
            />
          ))}
        </div>
      )}

      {/* Delete confirmation dialog */}
      <AlertDialog open={!!deleteTarget} onOpenChange={(open) => !open && setDeleteTarget(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete {deleteTarget?.filename}?</AlertDialogTitle>
            <AlertDialogDescription>
              This will remove all {deleteTarget?.chunk_count} chunks from the index. This action
              cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              variant="destructive"
              onClick={handleDeleteConfirm}
              disabled={isDeleting}
            >
              {isDeleting ? 'Deleting...' : 'Delete'}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  )
}
