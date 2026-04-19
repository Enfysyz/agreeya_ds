import { useState, useRef, useEffect } from "react";
import { Send, Sparkles, ChevronDown, ChevronUp } from "lucide-react";
import { Button } from "@/components/ui/button";

interface ChatInputProps {
  onSend: (message: string) => void;
  disabled: boolean;
}

const SUGGESTIONS = [
  "Who are the top 5 customers by order count?",
  "What products are out of stock?",
  "Show total revenue by country",
  "Which employees handle the most orders?",
];

export default function ChatInput({ onSend, disabled }: ChatInputProps) {
  const [input, setInput] = useState("");
  const [showSuggestions, setShowSuggestions] = useState(true);
  const [overflow, setOverflow] = useState<"hidden" | "auto">("hidden");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      const scrollHeight = textareaRef.current.scrollHeight;
      if (scrollHeight >= 120) {
        textareaRef.current.style.height = "120px";
        setOverflow("auto");
      } else {
        textareaRef.current.style.height = scrollHeight + "px";
        setOverflow("hidden");
      }
    }
  }, [input]);

  const handleSubmit = () => {
    const trimmed = input.trim();
    if (!trimmed || disabled) return;
    onSend(trimmed);
    setInput("");
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="w-full">
      {/* Suggestion chips - only show when empty */}
      {!input && !disabled && (
        <div className="px-4 pt-3 pb-1 flex flex-col gap-2">
          <button 
            onClick={() => setShowSuggestions(!showSuggestions)}
            className="flex items-center gap-1.5 text-xs text-muted-foreground hover:text-foreground w-fit transition-colors"
          >
            <Sparkles className="h-3 w-3 text-primary/70" />
            {showSuggestions ? "Hide suggested prompts" : "Show suggested prompts"}
            {showSuggestions ? <ChevronUp className="h-3 w-3 ml-0.5" /> : <ChevronDown className="h-3 w-3 ml-0.5" />}
          </button>
          
          {showSuggestions && (
            <div className="flex flex-wrap gap-1.5">
              {SUGGESTIONS.map((s) => (
                <button
                  key={s}
                  onClick={() => setInput(s)}
                  className="text-[11px] px-2.5 py-1 rounded-full border border-border text-muted-foreground hover:bg-accent hover:text-accent-foreground transition-colors cursor-pointer"
                >
                  {s}
                </button>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Input area */}
      <div className="p-3 flex items-end gap-2">
        <div className="flex-1 relative">
          <textarea
            ref={textareaRef}
            id="chat-input"
            rows={1}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={disabled}
            placeholder="Ask about your data…"
            style={{ overflowY: overflow }}
            className="w-full resize-none rounded-xl border border-border/60 bg-muted/20 px-4 py-2.5 text-sm placeholder:text-muted-foreground/50 focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary/40 transition-all disabled:opacity-50"
          />
        </div>
        <Button
          id="send-button"
          size="icon"
          onClick={handleSubmit}
          disabled={!input.trim() || disabled}
          className="h-10 w-10 rounded-xl shrink-0 shadow-sm"
        >
          <Send className="h-4 w-4" />
        </Button>
      </div>
    </div>
  );
}
