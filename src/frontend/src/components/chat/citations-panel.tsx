import { useState } from 'react'
import type { Citation } from '@/types/api'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Separator } from '@/components/ui/separator'
import { FileText, ChevronDown, ChevronUp } from 'lucide-react'

interface CitationsPanelProps {
  citations: Citation[]
}

function CitationCard({ citation }: { citation: Citation }) {
  const [expanded, setExpanded] = useState(false)
  const text = citation.chunk_text
  const isLong = text.length > 200
  const displayText = expanded || !isLong ? text : text.slice(0, 200) + '...'
  const relevancePercent = Math.round(citation.relevance_score * 100)

  return (
    <Card size="sm">
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-sm">
          <FileText className="h-3.5 w-3.5 shrink-0 text-muted-foreground" />
          <span className="truncate font-semibold">{citation.document_name}</span>
        </CardTitle>
        <div className="flex gap-2 text-xs">
          <Badge variant="secondary" className="text-xs">
            {citation.page_number != null ? `Page ${citation.page_number}` : 'N/A'}
          </Badge>
          <Badge variant="outline" className="text-xs">
            {relevancePercent}% relevant
          </Badge>
        </div>
      </CardHeader>
      <CardContent>
        <p className="whitespace-pre-wrap text-xs text-muted-foreground">{displayText}</p>
        {isLong && (
          <button
            type="button"
            onClick={() => setExpanded(!expanded)}
            className="mt-1 inline-flex items-center gap-1 text-xs text-primary hover:underline"
          >
            {expanded ? (
              <>Show less <ChevronUp className="h-3 w-3" /></>
            ) : (
              <>Show more <ChevronDown className="h-3 w-3" /></>
            )}
          </button>
        )}
      </CardContent>
    </Card>
  )
}

export function CitationsPanel({ citations }: CitationsPanelProps) {
  if (citations.length === 0) {
    return (
      <div className="flex h-full items-center justify-center p-4 text-sm text-muted-foreground">
        Select a message to view citations
      </div>
    )
  }

  const sorted = [...citations].sort((a, b) => b.relevance_score - a.relevance_score)

  return (
    <div className="flex flex-col gap-1 p-2">
      <h3 className="px-2 pb-1 text-sm font-semibold">
        Sources ({sorted.length})
      </h3>
      <Separator />
      <div className="mt-2 flex flex-col gap-3">
        {sorted.map((citation, i) => (
          <CitationCard key={i} citation={citation} />
        ))}
      </div>
    </div>
  )
}
