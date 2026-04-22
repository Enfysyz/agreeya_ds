import { useState } from 'react'
import { Bot, User, ChevronDown, ChevronRight } from 'lucide-react'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible'
import { Button } from '@/components/ui/button'
import ReactMarkdown from 'react-markdown'
import { ActivityLog } from './ActivityLog'
import type { ChatMessage as ChatMessageType } from '@/types'

interface ChatMessageProps {
  message: ChatMessageType
  onSourceSelect?: (url: string) => void
  selectedSourceUrl?: string | null
}

export function ChatMessage({ message, onSourceSelect, selectedSourceUrl }: ChatMessageProps) {
  const isUser = message.role === 'user'
  const [isLogsOpen, setIsLogsOpen] = useState(false)

  return (
    <div
      className={`flex gap-3 w-full ${isUser ? 'flex-row-reverse' : 'flex-row'}`}
      style={{
        animationName: 'fadeIn',
        animationDuration: '0.4s',
        animationTimingFunction: 'ease-out',
      }}
    >
      {/* Avatar */}
      <Avatar className={`h-8 w-8 shrink-0 mt-auto mb-1 ring-2 ring-offset-1 ${
        isUser
          ? 'ring-slate-200 bg-slate-100'
          : 'ring-indigo-200 bg-indigo-50'
      }`}>
        <AvatarFallback className={isUser ? 'bg-slate-100 text-slate-600' : 'bg-indigo-50 text-indigo-600'}>
          {isUser ? <User className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
        </AvatarFallback>
      </Avatar>

      {/* Content wrapper */}
      <div className={`flex flex-col max-w-[85%] ${isUser ? 'items-end' : 'items-start'}`}>
        <div className={`flex items-center gap-2 mb-1 px-1`}>
          <span className="text-xs font-medium text-muted-foreground">
            {isUser ? 'You' : 'Research Agent'}
          </span>
          <span className="text-[10px] text-muted-foreground/60 font-mono">
            {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
          </span>
        </div>

        {isUser ? (
          <div className="px-4 py-3 rounded-2xl bg-indigo-600 text-white rounded-br-sm shadow-sm">
            <p className="text-sm leading-relaxed whitespace-pre-wrap">{message.content}</p>
          </div>
        ) : (
          <div className="flex flex-col w-full gap-2 items-start">
            {/* Logs Area */}
            {message.logs.length > 0 && (
              <Collapsible
                open={message.isLoading ? true : isLogsOpen}
                onOpenChange={setIsLogsOpen}
                className="w-full min-w-[300px] bg-slate-50/50 border rounded-xl overflow-hidden shadow-sm"
              >
                {!message.isLoading && (
                  <CollapsibleTrigger asChild>
                    <Button variant="ghost" size="sm" className="w-full flex items-center justify-between p-3 h-auto rounded-none hover:bg-slate-100/80">
                      <span className="text-xs font-medium text-slate-600">Research Logs ({message.logs.length})</span>
                      {isLogsOpen ? <ChevronDown className="h-4 w-4 text-slate-400" /> : <ChevronRight className="h-4 w-4 text-slate-400" />}
                    </Button>
                  </CollapsibleTrigger>
                )}
                <CollapsibleContent className={message.isLoading ? "p-4" : "p-4 pt-0 border-t"}>
                  <ActivityLog 
                    logs={message.logs} 
                    isActive={message.isLoading} 
                    onSourceSelect={onSourceSelect}
                    selectedSourceUrl={selectedSourceUrl}
                  />
                </CollapsibleContent>
              </Collapsible>
            )}

            {/* Final report */}
            {message.content && (
              <div className="px-5 py-4 rounded-2xl bg-white border shadow-sm rounded-bl-sm prose prose-sm prose-slate max-w-none
                prose-headings:text-slate-800 prose-headings:font-semibold
                prose-p:text-slate-700 prose-p:leading-relaxed
                prose-a:text-indigo-600 prose-a:no-underline hover:prose-a:underline
                prose-strong:text-slate-800 prose-strong:font-semibold
                prose-li:text-slate-700
                prose-code:text-indigo-600 prose-code:bg-indigo-50 prose-code:px-1 prose-code:py-0.5 prose-code:rounded prose-code:text-xs
                prose-pre:bg-slate-50 prose-pre:border prose-pre:border-slate-200
                prose-blockquote:border-l-indigo-300 prose-blockquote:bg-indigo-50/50 prose-blockquote:rounded-r-lg
              ">
                <ReactMarkdown>{message.content}</ReactMarkdown>
              </div>
            )}

            {/* Loading indicator when still processing */}
            {message.isLoading && !message.content && message.logs.length === 0 && (
              <div className="px-4 py-3 rounded-2xl bg-white border shadow-sm rounded-bl-sm flex items-center gap-2">
                <div className="flex gap-1">
                  <span className="h-2 w-2 rounded-full bg-indigo-400 animate-bounce" style={{ animationDelay: '0ms' }} />
                  <span className="h-2 w-2 rounded-full bg-indigo-400 animate-bounce" style={{ animationDelay: '150ms' }} />
                  <span className="h-2 w-2 rounded-full bg-indigo-400 animate-bounce" style={{ animationDelay: '300ms' }} />
                </div>
                <span className="text-xs text-muted-foreground">Starting research...</span>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
