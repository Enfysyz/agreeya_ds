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
  id: string;
  agent: AgentName;
  label: string;
  icon: React.ElementType;
  status: "completed" | "error" | "running";
  data: Record<string, unknown> | null;
  timestamp: Date;
  durationMs?: number;
}

// ── Chat message model ──
export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  agentEvents: AgentEvent[];
  isStreaming: boolean;
  report?: string;
  timestamp: Date;
  workflowDurationMs?: number;
}

import {
  Building2,
  Swords,
  TrendingUp,
  DollarSign,
  CheckSquare,
  FileEdit,
  Microscope,
  Settings,
} from "lucide-react";

// ── Mapping of agent names to friendly labels & icons ──
export const AGENT_META: Record<
  string,
  { label: string; icon: React.ElementType; description: string }
> = {
  research_company: {
    label: "Company Researcher",
    icon: Building2,
    description: "Researches the company's core operations, products, and business model.",
  },
  research_competitor: {
    label: "Competitor Analyst",
    icon: Swords,
    description: "Analyzes the competitive landscape and rival positioning.",
  },
  research_market: {
    label: "Market Analyst",
    icon: TrendingUp,
    description: "Examines industry trends, market size, and growth opportunities.",
  },
  research_financial: {
    label: "Financial Analyst",
    icon: DollarSign,
    description: "Evaluates revenue, profitability, funding, and financial risks.",
  },
  validate_data: {
    label: "Data Validator",
    icon: CheckSquare,
    description: "QA engineer that validates research data completeness and accuracy.",
  },
  write_report: {
    label: "Report Writer",
    icon: FileEdit,
    description: "Synthesizes all validated data into a comprehensive report.",
  },
  critique_report: {
    label: "Report Critic",
    icon: Microscope,
    description: "Grades the report on quality, synthesis, and readability.",
  },
  system: {
    label: "System",
    icon: Settings,
    description: "System-level orchestration events.",
  },
};
