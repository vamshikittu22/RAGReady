import { useEffect, useRef } from 'react'
import type { ChatMessage } from '@/types/api'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Skeleton } from '@/components/ui/skeleton'
import { MessageBubble } from '@/components/chat/message-bubble'

interface MessageListProps {
  messages: ChatMessage[]
  selectedMessageIndex: number | null
  isLoading: boolean
  onSelectMessage: (index: number, message: ChatMessage) => void
}

export function MessageList({
  messages,
  selectedMessageIndex,
  isLoading,
  onSelectMessage,
}: MessageListProps) {
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages.length, isLoading])

  if (messages.length === 0 && !isLoading) {
    return (
      <div className="flex flex-1 items-center justify-center text-muted-foreground">
        <p>Ask a question to get started</p>
      </div>
    )
  }

  return (
    <ScrollArea className="flex-1 overflow-y-auto">
      <div className="flex flex-col gap-3 p-4">
        {messages.map((message, index) => (
          <MessageBubble
            key={index}
            message={message}
            isSelected={selectedMessageIndex === index}
            onSelect={(msg) => onSelectMessage(index, msg)}
          />
        ))}
        {isLoading && (
          <div className="flex justify-start">
            <div className="max-w-[80%] space-y-2 rounded-2xl rounded-bl-sm bg-muted px-4 py-3">
              <Skeleton className="h-4 w-48" />
              <Skeleton className="h-4 w-36" />
              <Skeleton className="h-4 w-24" />
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>
    </ScrollArea>
  )
}
