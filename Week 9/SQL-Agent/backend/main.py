from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import database

app = FastAPI(title="Analyst-in-the-Loop SQL Agent API")

class ChatRequest(BaseModel):
    message: str

@app.get("/health")
def health_check():
    return {"status": "Backend is running!"}

@app.get("/api/schema")
def get_schema():
    """Endpoint to verify the backend can see the database."""
    schema = database.get_database_schema()
    return {"schema": schema}

@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    # TODO: Connect this to the LangGraph Agent workflow
    # For now, we will just return a placeholder
    return {
        "reply": "I received your message. LangGraph agent is not yet wired up.",
        "sql_generated": None,
        "data_result": None
    }