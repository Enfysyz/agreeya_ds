// ── Agent names from the LangGraph workflow ──
export type AgentName =
  | "research_company"
  | "research_competitor"
  | "research_market"
  | "research_financial"
  | "validate_data"
  | "write_report"
  | "critique_report"
  | "system";

// ── SSE payload from the backend ──
export interface SSEPayload {
  agent: AgentName;
  status: "completed" | "error" | "done";
  data?: Record<string, unknown>;
  message?: string;
}

// ── Processed agent event for the UI ──
export interface AgentEvent {
  agent: AgentName;
  label: string;
  icon: string;
  status: "completed" | "error" | "running";
  data: Record<string, unknown> | null;
  timestamp: Date;
}

// ── Chat message model ──
export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  agentEvents: AgentEvent[];
  isStreaming: boolean;
  report?: string;
}

// ── Mapping of agent names to friendly labels & icons ──
export const AGENT_META: Record<
  string,
  { label: string; icon: string; description: string }
> = {
  research_company: {
    label: "Company Researcher",
    icon: "🏢",
    description: "Researches the company's core operations, products, and business model.",
  },
  research_competitor: {
    label: "Competitor Analyst",
    icon: "⚔️",
    description: "Analyzes the competitive landscape and rival positioning.",
  },
  research_market: {
    label: "Market Analyst",
    icon: "📊",
    description: "Examines industry trends, market size, and growth opportunities.",
  },
  research_financial: {
    label: "Financial Analyst",
    icon: "💰",
    description: "Evaluates revenue, profitability, funding, and financial risks.",
  },
  validate_data: {
    label: "Data Validator",
    icon: "✅",
    description: "QA engineer that validates research data completeness and accuracy.",
  },
  write_report: {
    label: "Report Writer",
    icon: "📝",
    description: "Synthesizes all validated data into a comprehensive report.",
  },
  critique_report: {
    label: "Report Critic",
    icon: "🔍",
    description: "Grades the report on quality, synthesis, and readability.",
  },
  system: {
    label: "System",
    icon: "⚙️",
    description: "System-level orchestration events.",
  },
};
