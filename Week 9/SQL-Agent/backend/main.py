from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import database

from langchain_core.messages import HumanMessage
from agent import agent_app

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
    try:
        initial_state = {
            "messages": [HumanMessage(content=request.message)],
            "sql_query": "",
            "agent_reply": "",
            "error": "",
            "data": {}
        }
        
        final_state = agent_app.invoke(initial_state) 
        
        return {
            # Now we return the actual LLM's conversational text!
            "reply": final_state.get("agent_reply", ""),
            "sql_generated": final_state.get("sql_query", ""),
            "data_result": final_state.get("data", {})
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))