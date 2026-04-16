import { useState, useRef, useEffect, useCallback } from "react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import {
  Brain,
  Send,
  FolderOpen,
  Sparkles,
  Zap,
  ArrowDown,
} from "lucide-react";
import { ChatMessage } from "@/components/ChatMessage";
import { CitationsPanel } from "@/components/CitationsPanel";
import { FilesPanel } from "@/components/FilesPanel";
import { queryDocuments, getIndexedFiles } from "@/lib/api";
import type { Message } from "@/components/ChatMessage";
import type { Citation } from "@/lib/api";

function App() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isQuerying, setIsQuerying] = useState(false);

  // Citations panel state
  const [activeCitations, setActiveCitations] = useState<Citation[]>([]);
  const [citationsOpen, setCitationsOpen] = useState(false);

  // Files panel state
  const [filesOpen, setFilesOpen] = useState(false);
  const [indexedFiles, setIndexedFiles] = useState<string[]>([]);
  const [totalFiles, setTotalFiles] = useState(0);
  const [filesLoading, setFilesLoading] = useState(false);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  const handleViewCitations = (citations: Citation[]) => {
    setActiveCitations(citations);
    setCitationsOpen(true);
    setFilesOpen(false);
  };

  const handleViewFiles = async () => {
    setCitationsOpen(false);
    setFilesOpen(true);
    setFilesLoading(true);
    try {
      const data = await getIndexedFiles();
      setIndexedFiles(data.indexed_files);
      setTotalFiles(data.total_files);
    } catch {
      setIndexedFiles([]);
      setTotalFiles(0);
    } finally {
      setFilesLoading(false);
    }
  };

  const handleSubmit = async () => {
    const query = input.trim();
    if (!query || isQuerying) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content: query,
    };

    const loadingMessage: Message = {
      id: (Date.now() + 1).toString(),
      role: "assistant",
      content: "",
      isLoading: true,
    };

    setMessages((prev) => [...prev, userMessage, loadingMessage]);
    setInput("");
    setIsQuerying(true);

    try {
      const response = await queryDocuments(query);
      const assistantMessage: Message = {
        id: (Date.now() + 2).toString(),
        role: "assistant",
        content: response.answer,
        citations: response.citations,
      };
      setMessages((prev) => [...prev.slice(0, -1), assistantMessage]);

      // Auto-open citations if we have them
      if (response.citations.length > 0) {
        setActiveCitations(response.citations);
        setCitationsOpen(true);
        setFilesOpen(false);
      }
    } catch (err) {
      const errorMessage: Message = {
        id: (Date.now() + 2).toString(),
        role: "assistant",
        content: `Sorry, I encountered an error processing your request. Please make sure the backend is running on port 8000.\n\nError: ${err instanceof Error ? err.message : "Unknown error"}`,
      };
      setMessages((prev) => [...prev.slice(0, -1), errorMessage]);
    } finally {
      setIsQuerying(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const hasMessages = messages.length > 0;

  return (
    <div className="h-screen flex flex-col overflow-hidden">
      {/* Top Bar */}
      <header className="flex-shrink-0 border-b border-border bg-card/50 backdrop-blur-md px-6 py-3">
        <div className="max-w-4xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-primary/80 to-accent/80 flex items-center justify-center pulse-glow">
              <Brain className="w-5 h-5 text-white" />
            </div>
            <div>
              <h1 className="text-sm font-bold tracking-tight">
                Knowledge Cortex
              </h1>
              <p className="text-[11px] text-muted-foreground">
                RAG-Powered Document Intelligence
              </p>
            </div>
          </div>

          <Button
            variant="outline"
            size="sm"
            onClick={handleViewFiles}
            className="text-xs gap-1.5 cursor-pointer"
            id="view-files-btn"
          >
            <FolderOpen className="w-3.5 h-3.5" />
            Documents
          </Button>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 overflow-hidden">
        {!hasMessages ? (
          /* Empty State */
          <div className="h-full flex flex-col items-center justify-center px-6">
            <div className="max-w-lg text-center space-y-6">
              <div className="w-16 h-16 mx-auto rounded-2xl bg-gradient-to-br from-primary/20 to-accent/20 flex items-center justify-center mb-2">
                <Sparkles className="w-8 h-8 text-primary" />
              </div>
              <div>
                <h2 className="text-2xl font-bold tracking-tight mb-2">
                  Ask your documents anything
                </h2>
                <p className="text-sm text-muted-foreground leading-relaxed">
                  Knowledge Cortex uses hybrid search and re-ranking to find the
                  most relevant passages from your indexed documents. Every
                  answer comes with verifiable citations.
                </p>
              </div>

              <Separator className="bg-border/30" />

              <div className="grid grid-cols-2 gap-3">
                {[
                  {
                    icon: Zap,
                    label: "Hybrid Search",
                    desc: "Dense vectors + BM25",
                  },
                  {
                    icon: Brain,
                    label: "Self-Correcting",
                    desc: "Hallucination-free answers",
                  },
                ].map((feature) => (
                  <div
                    key={feature.label}
                    className="p-3 rounded-xl bg-secondary/40 border border-border/30 text-left"
                  >
                    <feature.icon className="w-4 h-4 text-primary mb-1.5" />
                    <p className="text-xs font-medium">{feature.label}</p>
                    <p className="text-[11px] text-muted-foreground">
                      {feature.desc}
                    </p>
                  </div>
                ))}
              </div>

              <div className="flex items-center justify-center gap-1.5 text-xs text-muted-foreground/50">
                <ArrowDown className="w-3 h-3" />
                <span>Type a question below to get started</span>
              </div>
            </div>
          </div>
        ) : (
          /* Messages */
          <ScrollArea className="h-full">
            <div className="max-w-4xl mx-auto px-6 py-6 space-y-5">
              {messages.map((msg) => (
                <ChatMessage
                  key={msg.id}
                  message={msg}
                  onViewCitations={handleViewCitations}
                />
              ))}
              <div ref={messagesEndRef} />
            </div>
          </ScrollArea>
        )}
      </main>

      {/* Input Bar */}
      <footer className="flex-shrink-0 border-t border-border bg-card/50 backdrop-blur-md px-6 py-4">
        <div className="max-w-4xl mx-auto">
          <div className="flex items-end gap-3">
            <div className="flex-1 relative">
              <Textarea
                ref={textareaRef}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Ask a question about your documents..."
                className="min-h-[44px] max-h-[120px] resize-none bg-secondary/50 border-border/50 focus:border-primary/50 pr-4 text-sm placeholder:text-muted-foreground/50"
                rows={1}
                disabled={isQuerying}
                id="query-input"
              />
            </div>
            <Button
              onClick={handleSubmit}
              disabled={!input.trim() || isQuerying}
              size="icon"
              className="h-11 w-11 rounded-xl bg-primary hover:bg-primary/90 transition-all duration-200 disabled:opacity-30 flex-shrink-0 cursor-pointer"
              id="submit-btn"
            >
              <Send className="w-4 h-4" />
            </Button>
          </div>
          <p className="text-[10px] text-muted-foreground/40 mt-2 text-center">
            Shift+Enter for new line · Enter to send · Answers backed by document citations
          </p>
        </div>
      </footer>

      {/* Side Panels */}
      <CitationsPanel
        citations={activeCitations}
        isOpen={citationsOpen}
        onClose={() => setCitationsOpen(false)}
      />
      <FilesPanel
        files={indexedFiles}
        totalFiles={totalFiles}
        isOpen={filesOpen}
        isLoading={filesLoading}
        onClose={() => setFilesOpen(false)}
      />

      {/* Overlay when panel is open */}
      {(citationsOpen || filesOpen) && (
        <div
          className="fixed inset-0 bg-black/30 backdrop-blur-[2px] z-40 transition-opacity duration-300"
          onClick={() => {
            setCitationsOpen(false);
            setFilesOpen(false);
          }}
        />
      )}
    </div>
  );
}

export default App;
