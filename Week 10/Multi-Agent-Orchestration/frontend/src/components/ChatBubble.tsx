import { useState, useMemo } from "react";
import Markdown from "react-markdown";
import { Loader2 } from "lucide-react";
import { AgentWorkflowLog } from "@/components/AgentWorkflowLog";
import { AgentDetailPanel } from "@/components/AgentDetailPanel";
import type { ChatMessage } from "@/types";

interface ChatBubbleProps {
  message: ChatMessage;
}

export function ChatBubble({ message }: ChatBubbleProps) {
  const [selectedAgentKey, setSelectedAgentKey] = useState<string | null>(null);

  const selectedEvent = useMemo(() => {
    if (!selectedAgentKey) return null;
    return message.agentEvents.find(e => e.id === selectedAgentKey) || null;
  }, [selectedAgentKey, message.agentEvents]);

  if (message.role === "user") {
    return (
      <div className="chat-bubble chat-bubble--user" id={`message-${message.id}`}>
        <div className="chat-bubble-content chat-bubble-content--user">
          <div className="flex justify-between items-center mb-1 text-xs opacity-80">
            <span className="font-semibold">You</span>
            <span className="ml-4">{message.timestamp?.toLocaleTimeString()}</span>
          </div>
          <p className="chat-user-text">
            Analyze <strong>{message.content}</strong>
          </p>
        </div>
      </div>
    );
  }

  // Assistant message
  const hasReport = !!message.report && !message.isStreaming;

  return (
    <div className="chat-bubble chat-bubble--assistant" id={`message-${message.id}`}>
      <div className="assistant-layout">
        {/* Main content column */}
        <div className="assistant-main">
          <div className="flex items-center gap-2 mb-2">
            <span className="font-semibold text-sm">System</span>
            <span className="text-xs text-muted-foreground">{message.timestamp?.toLocaleTimeString()}</span>
          </div>

          {/* Agent workflow log (collapsible) */}
          {message.agentEvents.length > 0 && (
            <AgentWorkflowLog
              events={message.agentEvents}
              isStreaming={message.isStreaming}
              selectedAgent={selectedAgentKey}
              onSelectAgent={(key) =>
                setSelectedAgentKey((prev) => (prev === key ? null : key))
              }
            />
          )}

          {/* Loading indicator while streaming with no report yet */}
          {message.isStreaming && !message.report && (
            <div className="streaming-indicator">
              <Loader2 className="h-5 w-5 animate-spin text-primary" />
              <span>Agents are working on your analysis…</span>
            </div>
          )}

          {/* Final report */}
          {hasReport && (
            <div className="report-container">
              <div className="report-header">
                <span className="report-icon">📄</span>
                <h3 className="report-title">Analysis Report</h3>
              </div>
              <div className="report-content prose">
                <Markdown>{message.report}</Markdown>
              </div>
            </div>
          )}

          {/* Error content */}
          {!message.isStreaming && !message.report && message.content && (
            <div className="error-content">
              <p>{message.content}</p>
            </div>
          )}
        </div>

        {/* Right-side detail panel */}
        {selectedEvent && (
          <AgentDetailPanel
            event={selectedEvent}
            onClose={() => setSelectedAgentKey(null)}
          />
        )}
      </div>
    </div>
  );
}
