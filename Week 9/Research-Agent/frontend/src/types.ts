export interface LogEntry {
  type: 'log'
  message: string
  url?: string
  timestamp: Date
}

export interface SourceSummary {
  type: 'source_summary'
  url: string
  summary: string
}

export interface ResearchResult {
  type: 'complete'
  result: string
}

export type SSEEvent = LogEntry | SourceSummary | ResearchResult

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  logs: LogEntry[]
  summaries: SourceSummary[]
  isLoading: boolean
  timestamp: Date
}
