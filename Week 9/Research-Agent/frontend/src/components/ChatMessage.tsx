import { Bot, User } from 'lucide-react'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import ReactMarkdown from 'react-markdown'
import { ActivityLog } from './ActivityLog'
import type { ChatMessage as ChatMessageType } from '@/types'

interface ChatMessageProps {
  message: ChatMessageType
}

export function ChatMessage({ message }: ChatMessageProps) {
  const isUser = message.role === 'user'

  return (
    <div
      className={`flex gap-3 py-5 px-4 ${isUser ? '' : 'bg-muted/30'}`}
      style={{
        animationName: 'fadeIn',
        animationDuration: '0.4s',
        animationTimingFunction: 'ease-out',
      }}
    >
      {/* Avatar */}
      <Avatar className={`h-8 w-8 shrink-0 mt-0.5 ring-2 ring-offset-2 ${
        isUser
          ? 'ring-slate-300 bg-slate-100'
          : 'ring-indigo-200 bg-indigo-50'
      }`}>
        <AvatarFallback className={isUser ? 'bg-slate-100 text-slate-600' : 'bg-indigo-50 text-indigo-600'}>
          {isUser ? <User className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
        </AvatarFallback>
      </Avatar>

      {/* Content */}
      <div className="flex-1 min-w-0 space-y-1">
        <div className="flex items-center gap-2">
          <span className="text-sm font-semibold text-foreground">
            {isUser ? 'You' : 'Research Agent'}
          </span>
          <span className="text-[11px] text-muted-foreground font-mono">
            {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
          </span>
        </div>

        {/* User message or assistant response */}
        {isUser ? (
          <p className="text-sm text-foreground/90 leading-relaxed">{message.content}</p>
        ) : (
          <>
            {/* Activity logs */}
            <ActivityLog logs={message.logs} isActive={message.isLoading} />

            {/* Final report */}
            {message.content && (
              <div className="mt-4 prose prose-sm prose-slate max-w-none
                prose-headings:text-foreground prose-headings:font-semibold
                prose-p:text-foreground/80 prose-p:leading-relaxed
                prose-a:text-indigo-600 prose-a:no-underline hover:prose-a:underline
                prose-strong:text-foreground prose-strong:font-semibold
                prose-li:text-foreground/80
                prose-code:text-indigo-600 prose-code:bg-indigo-50 prose-code:px-1 prose-code:py-0.5 prose-code:rounded prose-code:text-xs
                prose-pre:bg-slate-50 prose-pre:border prose-pre:border-slate-200
                prose-blockquote:border-l-indigo-300 prose-blockquote:bg-indigo-50/50 prose-blockquote:rounded-r-lg
              ">
                <ReactMarkdown>{message.content}</ReactMarkdown>
              </div>
            )}

            {/* Loading indicator when still processing */}
            {message.isLoading && !message.content && message.logs.length === 0 && (
              <div className="flex items-center gap-2 mt-2">
                <div className="flex gap-1">
                  <span className="h-2 w-2 rounded-full bg-indigo-400 animate-bounce" style={{ animationDelay: '0ms' }} />
                  <span className="h-2 w-2 rounded-full bg-indigo-400 animate-bounce" style={{ animationDelay: '150ms' }} />
                  <span className="h-2 w-2 rounded-full bg-indigo-400 animate-bounce" style={{ animationDelay: '300ms' }} />
                </div>
                <span className="text-xs text-muted-foreground">Starting research...</span>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  )
}
