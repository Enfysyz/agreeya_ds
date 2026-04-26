import { useState, useCallback, useRef } from "react";
import type { AgentEvent, ChatMessage, SSEPayload } from "@/types";
import { AGENT_META } from "@/types";

let messageIdCounter = 0;
const nextId = () => `msg-${++messageIdCounter}`;

/**
 * Custom hook that manages the SSE connection to the /analyze endpoint
 * and converts raw SSE events into ChatMessage state.
 */
export function useAnalyze() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const abortRef = useRef<AbortController | null>(null);

  const analyze = useCallback(async (company: string) => {
    if (!company.trim()) return;

    // Add user message
    const userMsg: ChatMessage = {
      id: nextId(),
      role: "user",
      content: company.trim(),
      agentEvents: [],
      isStreaming: false,
      timestamp: new Date(),
    };

    // Add placeholder assistant message
    const assistantId = nextId();
    const assistantMsg: ChatMessage = {
      id: assistantId,
      role: "assistant",
      content: "",
      agentEvents: [],
      isStreaming: true,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMsg, assistantMsg]);
    setIsLoading(true);

    // Abort any in-flight request
    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;

    try {
      const res = await fetch("/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ company: company.trim() }),
        signal: controller.signal,
      });

      if (!res.ok || !res.body) {
        throw new Error(`Request failed with status ${res.status}`);
      }

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() || "";

        for (const line of lines) {
          const trimmed = line.trim();
          if (!trimmed.startsWith("data: ")) continue;

          const jsonStr = trimmed.slice(6);
          let payload: SSEPayload;
          try {
            payload = JSON.parse(jsonStr) as SSEPayload;
          } catch {
            continue;
          }

          // Process the SSE event
          if (payload.status === "done") {
            // Mark streaming complete
            setMessages((prev) =>
              prev.map((m) =>
                m.id === assistantId ? { ...m, isStreaming: false } : m
              )
            );
          } else if (payload.status === "error") {
            setMessages((prev) =>
              prev.map((m) =>
                m.id === assistantId
                  ? {
                      ...m,
                      isStreaming: false,
                      content: `❌ Error: ${payload.message || "Unknown error"}`,
                    }
                  : m
              )
            );
          } else if (payload.status === "completed") {
            const meta = AGENT_META[payload.agent] || {
              label: payload.agent,
              icon: "🤖",
            };

            const event: AgentEvent = {
              id: nextId(),
              agent: payload.agent,
              label: meta.label,
              icon: meta.icon,
              status: "completed",
              data: payload.data || null,
              timestamp: new Date(),
            };

            setMessages((prev) =>
              prev.map((m) => {
                if (m.id !== assistantId) return m;

                const updatedEvents = [...m.agentEvents, event];

                // If this is the report writer, extract the report
                let report = m.report;
                if (
                  payload.agent === "write_report" &&
                  payload.data?.report
                ) {
                  report = payload.data.report as string;
                }

                return {
                  ...m,
                  agentEvents: updatedEvents,
                  report,
                  content: report || m.content,
                };
              })
            );
          }
        }
      }
    } catch (err: unknown) {
      if (err instanceof Error && err.name === "AbortError") return;

      setMessages((prev) =>
        prev.map((m) =>
          m.id === assistantId
            ? {
                ...m,
                isStreaming: false,
                content: `❌ Connection error: ${err instanceof Error ? err.message : "Unknown"}`,
              }
            : m
        )
      );
    } finally {
      setIsLoading(false);
    }
  }, []);

  const clearMessages = useCallback(() => {
    abortRef.current?.abort();
    setMessages([]);
  }, []);

  return { messages, isLoading, analyze, clearMessages };
}
