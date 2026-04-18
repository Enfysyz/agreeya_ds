import type { ChatResponse, SchemaResponse } from "./types";

const API_BASE = "/api";

export async function fetchSchema(): Promise<SchemaResponse> {
  const res = await fetch(`${API_BASE}/schema`);
  if (!res.ok) throw new Error("Failed to fetch schema");
  return res.json();
}

export async function sendMessage(message: string): Promise<ChatResponse> {
  const res = await fetch(`${API_BASE}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Unknown error" }));
    throw new Error(err.detail || "Failed to send message");
  }
  return res.json();
}
