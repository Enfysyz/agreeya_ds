import { useState, useRef, useEffect, useCallback } from 'react'
import { Search } from 'lucide-react'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Separator } from '@/components/ui/separator'
import { ChatMessage } from '@/components/ChatMessage'
import { ChatInput } from '@/components/ChatInput'
import { WelcomeScreen } from '@/components/WelcomeScreen'
import { streamResearch } from '@/lib/api'
import type { ChatMessage as ChatMessageType, LogEntry } from '@/types'

function generateId() {
  return Math.random().toString(36).substring(2, 10)
}

export default function App() {
  const [messages, setMessages] = useState<ChatMessageType[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const scrollAreaRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = useCallback(() => {
    requestAnimationFrame(() => {
      const viewport = scrollAreaRef.current?.querySelector('[data-radix-scroll-area-viewport]')
      if (viewport) {
        viewport.scrollTop = viewport.scrollHeight
      }
    })
  }, [])

  // Auto-scroll on message updates
  useEffect(() => {
    scrollToBottom()
  }, [messages, scrollToBottom])

  const handleSubmit = async (topic: string) => {
    if (isLoading) return

    // Add user message
    const userMessage: ChatMessageType = {
      id: generateId(),
      role: 'user',
      content: topic,
      logs: [],
      isLoading: false,
      timestamp: new Date(),
    }

    // Add assistant placeholder
    const assistantId = generateId()
    const assistantMessage: ChatMessageType = {
      id: assistantId,
      role: 'assistant',
      content: '',
      logs: [],
      isLoading: true,
      timestamp: new Date(),
    }

    setMessages((prev) => [...prev, userMessage, assistantMessage])
    setIsLoading(true)

    await streamResearch(
      topic,
      // On log event
      (log: LogEntry) => {
        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === assistantId
              ? { ...msg, logs: [...msg.logs, log] }
              : msg
          )
        )
      },
      // On complete event
      (result) => {
        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === assistantId
              ? { ...msg, content: result.result, isLoading: false }
              : msg
          )
        )
        setIsLoading(false)
      },
      // On error
      (error) => {
        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === assistantId
              ? {
                  ...msg,
                  content: `⚠️ **Error:** ${error}`,
                  isLoading: false,
                }
              : msg
          )
        )
        setIsLoading(false)
      }
    )
  }

  const hasMessages = messages.length > 0

  return (
    <div className="flex flex-col h-screen bg-background">
      {/* Header */}
      <header className="shrink-0 border-b bg-background/80 backdrop-blur-sm sticky top-0 z-10">
        <div className="max-w-3xl mx-auto flex items-center gap-3 px-4 h-14">
          <div className="h-8 w-8 rounded-lg bg-gradient-to-br from-indigo-500 to-violet-600 flex items-center justify-center shadow-sm">
            <Search className="h-4 w-4 text-white" />
          </div>
          <div>
            <h1 className="text-sm font-semibold text-foreground leading-none">Deep Research Agent</h1>
            <p className="text-[11px] text-muted-foreground mt-0.5">AI-Powered Web Research</p>
          </div>
          {isLoading && (
            <div className="ml-auto flex items-center gap-2 text-xs text-indigo-600 font-medium">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-indigo-400 opacity-75" />
                <span className="relative inline-flex rounded-full h-2 w-2 bg-indigo-500" />
              </span>
              Researching...
            </div>
          )}
        </div>
        <Separator />
      </header>

      {/* Chat Area */}
      <ScrollArea ref={scrollAreaRef} className="flex-1">
        {hasMessages ? (
          <div className="max-w-3xl mx-auto">
            {messages.map((message) => (
              <ChatMessage key={message.id} message={message} />
            ))}
            {/* Bottom padding for scroll */}
            <div className="h-4" />
          </div>
        ) : (
          <WelcomeScreen onSuggestionClick={handleSubmit} />
        )}
      </ScrollArea>

      {/* Input Area */}
      <ChatInput onSubmit={handleSubmit} isLoading={isLoading} />
    </div>
  )
}
