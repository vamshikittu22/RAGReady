import { useState, useRef, useCallback } from 'react'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { Upload, FileUp } from 'lucide-react'
import { useDocuments } from '@/hooks/use-documents'
import { toast } from 'sonner'
import { cn } from '@/lib/utils'

const ACCEPTED_TYPES = '.pdf,.md,.txt,.html'

export function UploadDialog() {
  const [open, setOpen] = useState(false)
  const [file, setFile] = useState<File | null>(null)
  const [isDragOver, setIsDragOver] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const { uploadAsync, isUploading } = useDocuments()

  const handleFile = useCallback((selected: File | null) => {
    if (!selected) return
    const ext = '.' + selected.name.split('.').pop()?.toLowerCase()
    if (!ACCEPTED_TYPES.split(',').includes(ext)) {
      toast.error(`Unsupported file type: ${ext}. Accepted: ${ACCEPTED_TYPES}`)
      return
    }
    setFile(selected)
  }, [])

  function handleDragOver(e: React.DragEvent) {
    e.preventDefault()
    setIsDragOver(true)
  }

  function handleDragLeave(e: React.DragEvent) {
    e.preventDefault()
    setIsDragOver(false)
  }

  function handleDrop(e: React.DragEvent) {
    e.preventDefault()
    setIsDragOver(false)
    const dropped = e.dataTransfer.files[0]
    if (dropped) handleFile(dropped)
  }

  async function handleUpload() {
    if (!file) return
    try {
      const result = await uploadAsync(file)
      toast.success(`Document uploaded — ${result.chunk_count} chunks created`)
      setFile(null)
      setOpen(false)
      if (fileInputRef.current) fileInputRef.current.value = ''
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Upload failed'
      toast.error(message)
    }
  }

  function handleOpenChange(nextOpen: boolean) {
    setOpen(nextOpen)
    if (!nextOpen) {
      setFile(null)
      setIsDragOver(false)
      if (fileInputRef.current) fileInputRef.current.value = ''
    }
  }

  function formatFileSize(bytes: number): string {
    if (bytes < 1024) return bytes + ' B'
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
  }

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogTrigger render={<Button />}>
        <Upload className="mr-2 h-4 w-4" />
        Upload Document
      </DialogTrigger>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Upload Document</DialogTitle>
          <DialogDescription>
            Upload a document to index for RAG queries. Supported formats: PDF, Markdown, Text, HTML.
          </DialogDescription>
        </DialogHeader>

        {isUploading ? (
          <div className="space-y-3 py-4">
            <Skeleton className="h-4 w-3/4" />
            <Skeleton className="h-4 w-1/2" />
            <Skeleton className="h-4 w-2/3" />
          </div>
        ) : (
          <div
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
            className={cn(
              'flex cursor-pointer flex-col items-center justify-center gap-2 rounded-lg border-2 border-dashed p-8 text-center transition-colors',
              isDragOver
                ? 'border-primary bg-primary/5'
                : 'border-muted-foreground/25 hover:border-primary/50'
            )}
          >
            <FileUp className="h-8 w-8 text-muted-foreground" />
            <p className="text-sm text-muted-foreground">
              {file ? (
                <>
                  <span className="font-medium text-foreground">{file.name}</span>
                  <br />
                  <span className="text-xs">{formatFileSize(file.size)}</span>
                </>
              ) : (
                <>
                  Drag & drop a file here, or <span className="text-primary underline">browse</span>
                </>
              )}
            </p>
            <input
              ref={fileInputRef}
              type="file"
              accept={ACCEPTED_TYPES}
              onChange={(e) => handleFile(e.target.files?.[0] ?? null)}
              className="hidden"
            />
          </div>
        )}

        <DialogFooter>
          <Button
            onClick={handleUpload}
            disabled={!file || isUploading}
          >
            {isUploading ? 'Uploading...' : 'Upload'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
