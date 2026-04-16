const API_BASE = "http://localhost:8000";

export interface Citation {
  source: string;
  page?: number;
  score: number;
  content: string;
}

export interface QueryResponse {
  answer: string;
  citations: Citation[];
  retrieval_transparency: Citation[];
}

export interface FilesResponse {
  total_files: number;
  indexed_files: string[];
}

export async function queryDocuments(query: string): Promise<QueryResponse> {
  const res = await fetch(`${API_BASE}/query`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query }),
  });
  if (!res.ok) throw new Error(`Query failed: ${res.statusText}`);
  return res.json();
}

export async function getIndexedFiles(): Promise<FilesResponse> {
  const res = await fetch(`${API_BASE}/files`, {
    method: "GET",
    headers: { "Content-Type": "application/json" },
  });
  if (!res.ok) throw new Error(`Failed to fetch files: ${res.statusText}`);
  return res.json();
}
