import { Bot, User } from "lucide-react";
import type { ChatMessage as ChatMessageType } from "@/types";
import SqlCodeBlock from "./SqlCodeBlock";
import DataTable from "./DataTable";

interface ChatMessageProps {
  message: ChatMessageType;
}

function ThinkingIndicator() {
  return (
    <div className="flex items-center gap-1.5 py-2">
      <div className="thinking-dot w-1.5 h-1.5 rounded-full bg-primary/60" />
      <div className="thinking-dot w-1.5 h-1.5 rounded-full bg-primary/60" />
      <div className="thinking-dot w-1.5 h-1.5 rounded-full bg-primary/60" />
      <span className="text-xs text-muted-foreground ml-1">
        Analyzing your query…
      </span>
    </div>
  );
}

export default function ChatMessage({ message }: ChatMessageProps) {
  const isUser = message.role === "user";

  return (
    <div className={`message-enter flex gap-3 ${isUser ? "justify-end" : ""}`}>
      {/* Avatar */}
      {!isUser && (
        <div className="shrink-0 w-7 h-7 rounded-lg bg-primary/10 flex items-center justify-center mt-0.5">
          <Bot className="h-4 w-4 text-primary" />
        </div>
      )}

      {/* Content */}
      <div className={`flex flex-col gap-2.5 max-w-[85%] ${isUser ? "items-end" : ""}`}>
        {/* Text bubble */}
        <div
          className={`rounded-xl px-4 py-2.5 text-sm leading-relaxed ${
            isUser
              ? "bg-primary text-primary-foreground rounded-br-sm"
              : "bg-muted/60 text-foreground rounded-bl-sm"
          }`}
        >
          {message.isLoading ? <ThinkingIndicator /> : message.content}
        </div>

        {/* SQL Query */}
        {!message.isLoading && message.sqlQuery && (
          <div className="w-full">
            <SqlCodeBlock sql={message.sqlQuery} />
          </div>
        )}

        {/* Data Table */}
        {!message.isLoading &&
          message.dataResult &&
          Array.isArray(message.dataResult) &&
          message.dataResult.length > 0 && (
            <div className="w-full">
              <DataTable data={message.dataResult} />
            </div>
          )}

        {/* Timestamp */}
        <span className="text-[10px] text-muted-foreground/60 px-1">
          {message.timestamp.toLocaleTimeString([], {
            hour: "2-digit",
            minute: "2-digit",
          })}
        </span>
      </div>

      {/* User avatar */}
      {isUser && (
        <div className="shrink-0 w-7 h-7 rounded-lg bg-primary flex items-center justify-center mt-0.5">
          <User className="h-4 w-4 text-primary-foreground" />
        </div>
      )}
    </div>
  );
}
