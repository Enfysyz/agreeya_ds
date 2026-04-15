import threading
from fastapi import FastAPI
from pydantic import BaseModel
from src.rag_engine import ask_with_transparency, get_indexed_files
from src.watcher import start_watcher

app = FastAPI(title="Local RAG API")

class QueryRequest(BaseModel):
    query: str

@app.on_event("startup")
def startup_event():
    # Start the document watcher in a background thread
    watcher_thread = threading.Thread(target=start_watcher, daemon=True)
    watcher_thread.start()

@app.post("/query")
def ask_question(req: QueryRequest):
    # Call our new transparent engine
    result = ask_with_transparency(req.query)
    
    # Format the 3 documents used for the answer
    citations = [
        {
            "source": doc.metadata.get("source"),
            "page": doc.metadata.get("page"),
            "score": round(doc.metadata.get("rerank_score", 0), 4),
            "content": doc.page_content
        } 
        for doc in result["citations"]
    ]
    
    # Format the full 10 documents retrieved by hybrid search
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