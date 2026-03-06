import { useState } from 'react'
import type { ChatMessage, Citation } from '@/types/api'
import { useQueryRag } from '@/hooks/use-query-rag'
import { MessageList } from '@/components/chat/message-list'
import { ChatInput } from '@/components/chat/chat-input'
import { CitationsPanel } from '@/components/chat/citations-panel'
import { toast } from 'sonner'

export function ChatPanel() {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [selectedIndex, setSelectedIndex] = useState<number | null>(null)
  const { askAsync, isPending } = useQueryRag()

  const selectedCitations: Citation[] =
    selectedIndex != null ? messages[selectedIndex]?.citations ?? [] : []

  async function handleSubmit(question: string) {
    const userMessage: ChatMessage = { role: 'user', content: question }
    setMessages((prev) => [...prev, userMessage])

    try {
      const result = await askAsync(question)

      const assistantMessage: ChatMessage = result.refused
        ? {
            role: 'assistant',
            content: '',
            refused: true,
            refusalReason: result.reason,
            confidence: result.confidence,
            citations: [],
          }
        : {
            role: 'assistant',
            content: result.answer,
            citations: result.citations,
            confidence: result.confidence,
            refused: false,
          }

      setMessages((prev) => [...prev, assistantMessage])
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to get response'
      toast.error(message)
    }
  }

  function handleSelectMessage(index: number) {
    setSelectedIndex(index === selectedIndex ? null : index)
  }

  return (
    <div className="flex h-[calc(100vh-12rem)] flex-col gap-4 lg:flex-row">
      {/* Main chat area */}
      <div className="flex min-h-0 flex-1 flex-col rounded-lg border">
        <MessageList
          messages={messages}
          selectedMessageIndex={selectedIndex}
          isLoading={isPending}
          onSelectMessage={handleSelectMessage}
        />
        <div className="px-4 pb-3">
          <ChatInput onSubmit={handleSubmit} isPending={isPending} />
        </div>
      </div>

      {/* Citations sidebar */}
      <div className="h-64 shrink-0 overflow-y-auto rounded-lg border lg:h-auto lg:w-[30%]">
        <CitationsPanel citations={selectedCitations} />
      </div>
    </div>
  )
}
