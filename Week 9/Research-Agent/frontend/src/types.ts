export interface LogEntry {
  type: 'log'
  message: string
  url?: string
  timestamp: Date
}

export interface ResearchResult {
  type: 'complete'
  result: string
}

export type SSEEvent = LogEntry | ResearchResult

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  logs: LogEntry[]
  isLoading: boolean
  timestamp: Date
}
