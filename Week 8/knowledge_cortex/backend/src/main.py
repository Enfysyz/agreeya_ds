import threading
from fastapi import FastAPI
from pydantic import BaseModel
# Change these lines:
from src.rag_engine import get_rag_chain
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
    chain = get_rag_chain()
    response = chain.invoke({"input": req.query})
    
    # Extract answer and citations
    answer = response["answer"]
    sources = [{"source": doc.metadata.get("source"), "content": doc.page_content[:200] + "..."} 
               for doc in response["context"]]
    
    return {"answer": answer, "citations": sources}