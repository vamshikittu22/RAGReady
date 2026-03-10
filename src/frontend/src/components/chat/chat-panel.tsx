import { useState, useRef, useEffect } from 'react'
import type { ChatMessage, Citation } from '@/types/api'
import { useQueryRag, useQueryRagStream } from '@/hooks/use-query-rag'
import { MessageList } from '@/components/chat/message-list'
import { ChatInput } from '@/components/chat/chat-input'
import { CitationsPanel } from '@/components/chat/citations-panel'
import { toast } from 'sonner'

export function ChatPanel() {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [selectedIndex, setSelectedIndex] = useState<number | null>(null)
  const [useStreaming, setUseStreaming] = useState(true)
  const { askAsync, isPending } = useQueryRag()
  const { streamedAnswer, isStreaming, executeStream, clearStream } = useQueryRagStream()
  const streamingMessageIndex = useRef<number | null>(null)
  const isFinalized = useRef(false)

  const selectedCitations: Citation[] =
    selectedIndex != null ? messages[selectedIndex]?.citations ?? [] : []

  // Update the streaming message as tokens come in
  // Guard with isFinalized to prevent overwriting the finalized message
  useEffect(() => {
    if (
      isStreaming &&
      streamingMessageIndex.current !== null &&
      streamedAnswer &&
      !isFinalized.current
    ) {
      setMessages(prev => {
        const updated = [...prev]
        const idx = streamingMessageIndex.current!
        if (updated[idx]) {
          updated[idx] = {
            ...updated[idx],
            content: streamedAnswer,
          }
        }
        return updated
      })
    }
  }, [streamedAnswer, isStreaming])

  async function handleSubmit(question: string) {
    const userMessage: ChatMessage = { role: 'user', content: question }
    isFinalized.current = false

    try {
      if (useStreaming) {
        // Streaming mode
        const tempAssistantMessage: ChatMessage = {
          role: 'assistant',
          content: 'Thinking...',
          citations: [],
          confidence: 0,
          refused: false,
        }

        setMessages((prev) => {
          const next = [...prev, userMessage, tempAssistantMessage]
          streamingMessageIndex.current = next.length - 1
          return next
        })

        const result = await executeStream(question)

        // Mark as finalized BEFORE setting state to prevent useEffect overwrite
        isFinalized.current = true

        // Finalize with complete data from the done event
        if (result && streamingMessageIndex.current !== null) {
          const idx = streamingMessageIndex.current
          setMessages(prev => {
            const updated = [...prev]
            if (updated[idx]) {
              if (result.refused) {
                updated[idx] = {
                  role: 'assistant',
                  content: '',
                  refused: true,
                  refusalReason: result.reason,
                  confidence: result.confidence,
                  citations: [],
                }
              } else {
                updated[idx] = {
                  role: 'assistant',
                  content: result.answer || updated[idx].content,
                  citations: result.citations || [],
                  confidence: result.confidence,
                  refused: false,
                }
              }
            }
            return updated
          })
        }
        streamingMessageIndex.current = null
        clearStream()
      } else {
        // Non-streaming mode (original)
        setMessages((prev) => [...prev, userMessage])
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
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to get response'
      toast.error(message)
      // Clean up if we were streaming
      if (streamingMessageIndex.current !== null) {
        setMessages(prev => prev.filter((_, i) => i !== streamingMessageIndex.current!))
        streamingMessageIndex.current = null
        isFinalized.current = false
        clearStream()
      }
    }
  }

  function handleSelectMessage(index: number) {
    setSelectedIndex(index === selectedIndex ? null : index)
  }

  return (
    <div className="flex h-[calc(100vh-12rem)] flex-col gap-4 lg:flex-row">
      {/* Main chat area */}
      <div className="flex min-h-0 flex-1 flex-col rounded-lg border">
        <div className="flex items-center justify-between border-b px-4 py-2">
          <span className="text-sm text-muted-foreground">Chat</span>
          <label className="flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              checked={useStreaming}
              onChange={(e) => setUseStreaming(e.target.checked)}
              className="rounded border"
            />
            <span className="text-muted-foreground">Stream response</span>
          </label>
        </div>
        <MessageList
          messages={messages}
          selectedMessageIndex={selectedIndex}
          isLoading={isPending || isStreaming}
          onSelectMessage={handleSelectMessage}
        />
        <div className="px-4 pb-3">
          <ChatInput onSubmit={handleSubmit} isPending={isPending || isStreaming} />
        </div>
      </div>

      {/* Citations sidebar */}
      <div className="h-64 shrink-0 overflow-y-auto rounded-lg border lg:h-auto lg:w-[30%]">
        <CitationsPanel citations={selectedCitations} />
      </div>
    </div>
  )
}
