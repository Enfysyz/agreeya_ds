export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  sqlQuery?: string;
  dataResult?: Record<string, unknown>[];
  timestamp: Date;
  isLoading?: boolean;
}

export interface ChatResponse {
  reply: string;
  sql_generated: string;
  data_result: Record<string, unknown>[];
}

export interface SchemaResponse {
  schema: string;
}

export interface ParsedTable {
  name: string;
  columns: ParsedColumn[];
}

export interface ParsedColumn {
  name: string;
  type: string;
  key?: "PK" | "FK";
}
