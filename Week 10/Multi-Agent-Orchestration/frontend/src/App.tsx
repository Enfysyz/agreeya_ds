import { useRef, useEffect } from "react";
import { ChatInput } from "@/components/ChatInput";
import { ChatBubble } from "@/components/ChatBubble";
import { useAnalyze } from "@/hooks/useAnalyze";
import { ScrollArea } from "@/components/ui/scroll-area";
import { BrainCircuit, Sparkles } from "lucide-react";
import "./App.css";

function App() {
  const { messages, isLoading, analyze } = useAnalyze();
  const scrollRef = useRef<HTMLDivElement>(null);

  // Auto-scroll on new messages
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const isEmpty = messages.length === 0;

  return (
    <div className="app-shell">
      {/* Header */}
      <header className="app-header" id="app-header">
        <div className="header-brand">
          <div className="header-logo">
            <BrainCircuit className="h-6 w-6" />
          </div>
          <div>
            <h1 className="header-title">Multi-Agent Intelligence</h1>
            <p className="header-subtitle">Powered by LangGraph Orchestration</p>
          </div>
        </div>
      </header>

      {/* Chat area */}
      <ScrollArea className="chat-scroll-area" ref={scrollRef}>
        <div className="chat-container">
          {isEmpty ? (
            <div className="empty-state" id="empty-state">
              <div className="empty-icon-wrapper">
                <Sparkles className="empty-icon" />
              </div>
              <h2 className="empty-title">Company Intelligence Engine</h2>
              <p className="empty-subtitle">
                Enter any company name to generate a comprehensive analysis report using our multi-agent AI system.
              </p>
              <div className="empty-agents">
                <div className="empty-agent-chip">🏢 Company Research</div>
                <div className="empty-agent-chip">⚔️ Competitor Analysis</div>
                <div className="empty-agent-chip">📊 Market Analysis</div>
                <div className="empty-agent-chip">💰 Financial Analysis</div>
                <div className="empty-agent-chip">✅ Data Validation</div>
                <div className="empty-agent-chip">📝 Report Synthesis</div>
              </div>
              <div className="empty-suggestions">
                <p className="empty-suggestions-label">Try analyzing:</p>
                <div className="empty-suggestions-list">
                  {["Tesla", "Stripe", "Notion", "OpenAI"].map((name) => (
                    <button
                      key={name}
                      onClick={() => analyze(name)}
                      className="suggestion-chip"
                      id={`suggestion-${name.toLowerCase()}`}
                    >
                      {name}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            <div className="messages-list">
              {messages.map((msg) => (
                <ChatBubble key={msg.id} message={msg} />
              ))}
            </div>
          )}
        </div>
      </ScrollArea>

      {/* Input area */}
      <div className="input-dock" id="input-dock">
        <ChatInput onSubmit={analyze} isLoading={isLoading} />
      </div>
    </div>
  );
}

export default App;
