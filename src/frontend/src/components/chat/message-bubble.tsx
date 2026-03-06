import type { ChatMessage } from '@/types/api'
import { ConfidenceBadge } from '@/components/shared/confidence-badge'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { cn } from '@/lib/utils'
import { AlertTriangle } from 'lucide-react'

interface MessageBubbleProps {
  message: ChatMessage
  isSelected: boolean
  onSelect: (message: ChatMessage) => void
}

export function MessageBubble({ message, isSelected, onSelect }: MessageBubbleProps) {
  const isUser = message.role === 'user'
  const isRefused = message.refused === true

  if (isUser) {
    return (
      <div className="flex justify-end">
        <div className="max-w-[80%] rounded-2xl rounded-br-sm bg-primary px-4 py-2.5 text-primary-foreground">
          <p className="whitespace-pre-wrap text-sm">{message.content}</p>
        </div>
      </div>
    )
  }

  // Assistant message
  if (isRefused) {
    return (
      <div className="flex justify-start">
        <div className="max-w-[80%]">
          <Alert className="border-amber-200 bg-amber-50 dark:border-amber-800 dark:bg-amber-950/30">
            <AlertTriangle className="h-4 w-4 text-amber-600 dark:text-amber-400" />
            <AlertTitle className="text-amber-800 dark:text-amber-300">Unable to Answer</AlertTitle>
            <AlertDescription className="text-amber-700 dark:text-amber-400">
              {message.refusalReason || 'Insufficient evidence to provide a grounded answer.'}
            </AlertDescription>
          </Alert>
        </div>
      </div>
    )
  }

  return (
    <div className="flex justify-start">
      <button
        type="button"
        onClick={() => onSelect(message)}
        className={cn(
          'max-w-[80%] cursor-pointer rounded-2xl rounded-bl-sm bg-muted px-4 py-2.5 text-left transition-shadow hover:ring-2 hover:ring-ring/30',
          isSelected && 'ring-2 ring-primary/50'
        )}
      >
        <p className="whitespace-pre-wrap text-sm">{message.content}</p>
        {message.confidence != null && (
          <div className="mt-2">
            <ConfidenceBadge confidence={message.confidence} />
          </div>
        )}
      </button>
    </div>
  )
}
