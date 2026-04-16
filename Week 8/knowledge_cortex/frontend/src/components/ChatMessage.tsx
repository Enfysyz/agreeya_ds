import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Brain, User } from "lucide-react";
import type { Citation } from "@/lib/api";

export interface CitationsPanelData {
  all: Citation[];
  used: Citation[];
}

export interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  citationsData?: CitationsPanelData;
  isLoading?: boolean;
}

interface ChatMessageProps {
  message: Message;
  onViewCitations?: (data: CitationsPanelData) => void;
}

export function ChatMessage({ message, onViewCitations }: ChatMessageProps) {
  const isUser = message.role === "user";
  const totalCitations = message.citationsData?.all.length ?? 0;

  return (
    <div
      className={`flex gap-3 animate-fade-in ${
        isUser ? "justify-end" : "justify-start"
      }`}
    >
      {!isUser && (
        <div className="flex-shrink-0 w-8 h-8 rounded-lg bg-primary/10 border border-primary/15 flex items-center justify-center mt-1">
          <Brain className="w-4 h-4 text-primary" />
        </div>
      )}

      <div className={`max-w-[75%] ${isUser ? "order-first" : ""}`}>
        <Card
          className={`border shadow-none ${
            isUser
              ? "bg-primary/8 border-primary/20"
              : "bg-card border-border"
          }`}
        >
          <CardContent className="p-4">
            {message.isLoading ? (
              <div className="flex items-center gap-2">
                <div className="flex gap-1">
                  <span className="w-2 h-2 rounded-full bg-primary/60 animate-bounce [animation-delay:0ms]" />
                  <span className="w-2 h-2 rounded-full bg-primary/60 animate-bounce [animation-delay:150ms]" />
                  <span className="w-2 h-2 rounded-full bg-primary/60 animate-bounce [animation-delay:300ms]" />
                </div>
                <span className="text-sm text-muted-foreground">
                  Searching documents...
                </span>
              </div>
            ) : (
              <>
                <p className="text-sm leading-relaxed whitespace-pre-wrap">
                  {message.content}
                </p>
                {message.citationsData && totalCitations > 0 && (
                  <button
                    onClick={() => onViewCitations?.(message.citationsData!)}
                    className="mt-3 inline-flex items-center gap-1.5 text-xs text-primary hover:text-primary/80 transition-colors cursor-pointer"
                  >
                    <Badge
                      variant="secondary"
                      className="bg-primary/10 text-primary hover:bg-primary/20 transition-colors text-xs px-2 py-0.5"
                    >
                      {totalCitations} source{totalCitations > 1 ? "s" : ""}
                    </Badge>
                    <span className="text-muted-foreground">
                      — Click to view citations
                    </span>
                  </button>
                )}
              </>
            )}
          </CardContent>
        </Card>
      </div>

      {isUser && (
        <div className="flex-shrink-0 w-8 h-8 rounded-lg bg-secondary border border-border flex items-center justify-center mt-1">
          <User className="w-4 h-4 text-secondary-foreground" />
        </div>
      )}
    </div>
  );
}
