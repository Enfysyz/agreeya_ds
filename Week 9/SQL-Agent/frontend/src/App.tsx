import { useState, useRef, useEffect } from "react";
import {
  PanelLeftClose,
  PanelLeftOpen,
  TerminalSquare,
  Zap,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import SchemaPanel from "@/components/SchemaPanel";
import ChatMessage from "@/components/ChatMessage";
import ChatInput from "@/components/ChatInput";
import { sendMessage } from "@/api";
import type { ChatMessage as ChatMessageType } from "@/types";

function App() {
  const [messages, setMessages] = useState<ChatMessageType[]>([]);
  const [loading, setLoading] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const scrollRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    if (scrollRef.current) {
      const el = scrollRef.current.querySelector(
        "[data-radix-scroll-area-viewport]"
      );
      if (el) {
        el.scrollTop = el.scrollHeight;
      }
    }
  }, [messages]);

  const handleSend = async (text: string) => {
    const userMsg: ChatMessageType = {
      id: crypto.randomUUID(),
      role: "user",
      content: text,
      timestamp: new Date(),
    };

    const loadingMsg: ChatMessageType = {
      id: crypto.randomUUID(),
      role: "assistant",
      content: "",
      timestamp: new Date(),
      isLoading: true,
    };

    setMessages((prev) => [...prev, userMsg, loadingMsg]);
    setLoading(true);

    try {
      const res = await sendMessage(text);
      const assistantMsg: ChatMessageType = {
        id: loadingMsg.id,
        role: "assistant",
        content: res.reply,
        sqlQuery: res.sql_generated || undefined,
        dataResult: Array.isArray(res.data_result) ? res.data_result : undefined,
        timestamp: new Date(),
      };

      setMessages((prev) =>
        prev.map((m) => (m.id === loadingMsg.id ? assistantMsg : m))
      );
    } catch (err) {
      const errorMsg: ChatMessageType = {
        id: loadingMsg.id,
        role: "assistant",
        content: `Sorry, something went wrong: ${
          err instanceof Error ? err.message : "Unknown error"
        }`,
        timestamp: new Date(),
      };
      setMessages((prev) =>
        prev.map((m) => (m.id === loadingMsg.id ? errorMsg : m))
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="h-screen flex overflow-hidden bg-background">
      {/* Sidebar */}
      <div
        className={`${
          sidebarOpen ? "w-[300px]" : "w-0"
        } transition-all duration-300 ease-in-out overflow-hidden border-r border-border/50 bg-card shrink-0`}
      >
        <SchemaPanel />
      </div>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Top Bar */}
        <header className="h-13 shrink-0 border-b border-border/50 bg-card/80 backdrop-blur-sm flex items-center px-4 gap-3">
          <Button
            id="toggle-sidebar"
            variant="ghost"
            size="icon"
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="h-8 w-8 shrink-0"
          >
            {sidebarOpen ? (
              <PanelLeftClose className="h-4 w-4" />
            ) : (
              <PanelLeftOpen className="h-4 w-4" />
            )}
          </Button>

          <Separator orientation="vertical" className="h-5" />

          <div className="flex items-center gap-2">
            <div className="flex items-center justify-center w-7 h-7 rounded-lg bg-gradient-to-br from-primary/20 to-primary/5">
              <TerminalSquare className="h-4 w-4 text-primary" />
            </div>
            <div>
              <h1 className="text-sm font-semibold tracking-tight">
                SQL Agent
              </h1>
              <p className="text-[11px] text-muted-foreground leading-none">
                Natural language → SQL • Northwind Database
              </p>
            </div>
          </div>

          <div className="ml-auto flex items-center gap-1.5 text-[11px] text-muted-foreground">
            <Zap className="h-3 w-3 text-amber-500" />
            Powered by Llama 3
          </div>
        </header>

        {/* Messages */}
        <ScrollArea ref={scrollRef} className="flex-1">
          <div className="max-w-3xl mx-auto px-4 py-6 space-y-6">
            {messages.length === 0 && (
              <EmptyState />
            )}
            {messages.map((msg) => (
              <ChatMessage key={msg.id} message={msg} />
            ))}
          </div>
        </ScrollArea>

        {/* Input */}
        <div className="max-w-3xl mx-auto w-full">
          <ChatInput onSend={handleSend} disabled={loading} />
        </div>
      </div>
    </div>
  );
}

function EmptyState() {
  return (
    <div className="flex flex-col items-center justify-center py-20 gap-4 text-center">
      <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-primary/15 to-primary/5 flex items-center justify-center shadow-sm">
        <TerminalSquare className="h-8 w-8 text-primary/70" />
      </div>
      <div className="space-y-1.5">
        <h2 className="text-lg font-semibold tracking-tight">
          Ask anything about your data
        </h2>
        <p className="text-sm text-muted-foreground max-w-sm">
          Type a natural language question and the agent will generate SQL,
          execute it, and return the results in a table.
        </p>
      </div>
      <div className="flex flex-wrap gap-2 mt-2 max-w-md justify-center">
        {[
          "📊 View schema sidebar",
          "🔍 Ask data questions",
          "⚡ Get instant SQL + results",
        ].map((tip) => (
          <span
            key={tip}
            className="text-[11px] px-3 py-1.5 rounded-full bg-muted/60 text-muted-foreground"
          >
            {tip}
          </span>
        ))}
      </div>
    </div>
  );
}

export default App;
