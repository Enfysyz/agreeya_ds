import { useState, useRef, useEffect, useCallback } from 'react'
import { Search } from 'lucide-react'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Separator } from '@/components/ui/separator'
import { ChatMessage } from '@/components/ChatMessage'
import { ChatInput } from '@/components/ChatInput'
import { WelcomeScreen } from '@/components/WelcomeScreen'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { streamResearch } from '@/lib/api'
import type { ChatMessage as ChatMessageType, LogEntry, SourceSummary } from '@/types'

function generateId() {
  return Math.random().toString(36).substring(2, 10)
}

export default function App() {
  const [messages, setMessages] = useState<ChatMessageType[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [selectedSourceUrl, setSelectedSourceUrl] = useState<string | null>(null)
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
      summaries: [],
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
      summaries: [],
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
      // On summary event
      (summary: SourceSummary) => {
        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === assistantId
              ? { ...msg, summaries: [...msg.summaries, summary] }
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
  const allSummaries = messages.flatMap(m => m.summaries || [])

  return (
    <div className="flex flex-col h-screen bg-background overflow-hidden">
      {/* Header */}
      <header className="shrink-0 border-b bg-background/80 backdrop-blur-sm z-10">
        <div className="max-w-7xl mx-auto flex items-center gap-3 px-4 h-14">
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

      {/* Main Content Area */}
      <div className="flex-1 flex min-h-0 overflow-hidden">
        {/* Left Column: Chat Area */}
        <div className="flex-1 flex flex-col min-w-0 overflow-hidden relative">
          <ScrollArea ref={scrollAreaRef} className="flex-1 min-h-0">
            {hasMessages ? (
              <div className="max-w-4xl mx-auto py-6">
                <div className="flex flex-col space-y-4 px-4">
                  {messages.map((message) => (
                    <ChatMessage 
                      key={message.id} 
                      message={message} 
                      onSourceSelect={setSelectedSourceUrl}
                      selectedSourceUrl={selectedSourceUrl}
                    />
                  ))}
                </div>
                {/* Bottom padding for scroll */}
                <div className="h-4" />
              </div>
            ) : (
              <WelcomeScreen onSuggestionClick={handleSubmit} />
            )}
          </ScrollArea>

          {/* Input Area */}
          <div className="shrink-0 bg-gradient-to-t from-background to-transparent pb-4 pt-2">
            <ChatInput onSubmit={handleSubmit} isLoading={isLoading} />
          </div>
        </div>

        {/* Right Column: Source Summaries */}
        {allSummaries.length > 0 && (
          <div className="w-[400px] shrink-0 border-l bg-muted/20 flex flex-col min-h-0 overflow-hidden">
            <div className="p-4 border-b bg-background shrink-0">
              <h2 className="font-semibold text-sm">Source Summary</h2>
              <p className="text-xs text-muted-foreground mt-1">Select a source from the logs to view its details</p>
            </div>
            <ScrollArea className="flex-1 min-h-0">
              <div className="p-4">
                {selectedSourceUrl ? (
                  allSummaries.filter(s => s.url === selectedSourceUrl).length > 0 ? (
                    allSummaries.filter(s => s.url === selectedSourceUrl).map((summary, idx) => {
                      let hostname = summary.url
                      try {
                        hostname = new URL(summary.url).hostname
                      } catch {}
                      return (
                        <Card key={idx} className="bg-background shadow-sm border-muted mb-4">
                          <CardHeader className="p-3 pb-2">
                            <CardTitle className="text-sm font-medium text-indigo-600 truncate" title={summary.url}>
                              <a href={summary.url} target="_blank" rel="noreferrer" className="hover:underline">
                                {hostname}
                              </a>
                            </CardTitle>
                          </CardHeader>
                          <CardContent className="p-3 pt-0">
                            <p className="text-xs text-foreground/80 leading-relaxed whitespace-pre-wrap">
                              {summary.summary}
                            </p>
                          </CardContent>
                        </Card>
                      )
                    })
                  ) : (
                    <div className="text-center text-sm text-slate-500 mt-10">No summary available for this source.</div>
                  )
                ) : (
                  <div className="flex flex-col items-center justify-center h-40 text-center px-4 mt-10">
                    <Search className="h-8 w-8 text-slate-300 mb-3" />
                    <p className="text-sm text-slate-500 font-medium">No source selected</p>
                    <p className="text-xs text-slate-400 mt-1">Expand a source in the research logs to view its summary here.</p>
                  </div>
                )}
              </div>
            </ScrollArea>
          </div>
        )}
      </div>
    </div>
  )
}
