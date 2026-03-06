import type { DocumentInfo } from '@/types/api'
import { Card, CardContent, CardHeader, CardTitle, CardAction } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Trash2, FileText } from 'lucide-react'

interface DocumentCardProps {
  document: DocumentInfo
  onDelete: (id: string) => void
  isDeleting: boolean
}

function truncateFilename(name: string, maxLength = 30): string {
  if (name.length <= maxLength) return name
  const ext = name.lastIndexOf('.')
  if (ext > 0 && name.length - ext <= 5) {
    const extension = name.slice(ext)
    const available = maxLength - extension.length - 3
    return name.slice(0, available) + '...' + extension
  }
  return name.slice(0, maxLength - 3) + '...'
}

export function DocumentCard({ document: doc, onDelete, isDeleting }: DocumentCardProps) {
  return (
    <Card className="transition-shadow hover:shadow-md">
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-sm">
          <FileText className="h-4 w-4 shrink-0 text-muted-foreground" />
          <span className="truncate" title={doc.filename}>
            {truncateFilename(doc.filename)}
          </span>
        </CardTitle>
        <CardAction>
          <Button
            variant="ghost"
            size="icon-sm"
            onClick={() => onDelete(doc.document_id)}
            disabled={isDeleting}
            className="text-muted-foreground hover:text-destructive"
          >
            <Trash2 className="h-4 w-4" />
            <span className="sr-only">Delete {doc.filename}</span>
          </Button>
        </CardAction>
      </CardHeader>
      <CardContent>
        <div className="flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
          <Badge variant="secondary" className="text-xs">
            {doc.file_type}
          </Badge>
          <span>{doc.chunk_count} chunks</span>
          <span className="text-border">|</span>
          <span>{new Date(doc.created_at).toLocaleDateString()}</span>
        </div>
      </CardContent>
    </Card>
  )
}
