import { useState, useRef, type KeyboardEvent } from 'react'
import { Send, Loader2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'

interface ChatInputProps {
  onSubmit: (message: string) => void
  isLoading: boolean
}

export function ChatInput({ onSubmit, isLoading }: ChatInputProps) {
  const [input, setInput] = useState('')
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  const handleSubmit = () => {
    const trimmed = input.trim()
    if (!trimmed || isLoading) return
    onSubmit(trimmed)
    setInput('')
    // Reset textarea height
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
    }
  }

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit()
    }
  }

  const handleInput = () => {
    const textarea = textareaRef.current
    if (textarea) {
      textarea.style.height = 'auto'
      textarea.style.height = `${Math.min(textarea.scrollHeight, 160)}px`
    }
  }

  return (
    <div className="border-t bg-background/80 backdrop-blur-sm p-4">
      <div className="max-w-3xl mx-auto">
        <div className="relative flex items-end gap-2 rounded-2xl border border-border bg-background shadow-sm
          focus-within:ring-2 focus-within:ring-indigo-200 focus-within:border-indigo-300 transition-all duration-200 px-4 py-3">
          <Textarea
            ref={textareaRef}
            id="research-input"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            onInput={handleInput}
            placeholder="What would you like to research?"
            disabled={isLoading}
            className="flex-1 min-h-[24px] max-h-[160px] resize-none border-0 bg-transparent p-0
              focus-visible:ring-0 focus-visible:ring-offset-0 text-sm placeholder:text-muted-foreground/60
              scrollbar-thin"
            rows={1}
          />
          <Button
            id="submit-research"
            onClick={handleSubmit}
            disabled={!input.trim() || isLoading}
            size="icon"
            className="h-8 w-8 shrink-0 rounded-xl bg-indigo-600 hover:bg-indigo-700
              disabled:bg-muted disabled:text-muted-foreground transition-all duration-200
              shadow-sm hover:shadow-md"
          >
            {isLoading ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Send className="h-4 w-4" />
            )}
          </Button>
        </div>
        <p className="text-[11px] text-muted-foreground/60 text-center mt-2">
          Press <kbd className="px-1 py-0.5 rounded bg-muted text-[10px] font-mono">Enter</kbd> to send
          · <kbd className="px-1 py-0.5 rounded bg-muted text-[10px] font-mono">Shift+Enter</kbd> for new line
        </p>
      </div>
    </div>
  )
}
