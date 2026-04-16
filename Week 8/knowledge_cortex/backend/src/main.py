import threading
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware # <-- NEW IMPORT
from pydantic import BaseModel
from src.rag_engine import ask_with_transparency, get_indexed_files
from src.watcher import start_watcher

app = FastAPI(title="Local RAG API")

# --- NEW: ENABLE CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, change this to your frontend URL (e.g., "http://localhost:5173")
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# ------------------------

class QueryRequest(BaseModel):
    query: str

@app.on_event("startup")
def startup_event():
    watcher_thread = threading.Thread(target=start_watcher, daemon=True)
    watcher_thread.start()

@app.post("/query")
def ask_question(req: QueryRequest):
    result = ask_with_transparency(req.query)
    
    citations = [
        {
            "source": doc.metadata.get("source"),
            "page": doc.metadata.get("page"),
            "score": round(doc.metadata.get("rerank_score", 0), 4),
            "content": doc.page_content
        } 
        for doc in result["citations"]
    ]
    
    all_retrieved = [
        {
            "source": doc.metadata.get("source"),
            "page": doc.metadata.get("page"),
            "score": round(doc.metadata.get("rerank_score", 0), 4),
            "content": doc.page_content
        } 
        for doc in result["all_retrieved_docs"]
    ]
    
    return {
        "answer": result["answer"], 
        "citations": citations,
        "retrieval_transparency": all_retrieved
    }

@app.get("/files")
def list_indexed_files():
    files = get_indexed_files()
    return {
        "total_files": len(files),
        "indexed_files": files
    }