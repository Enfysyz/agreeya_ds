from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import database

from langchain_core.messages import HumanMessage
from agent import agent_app

import uuid # Add this at the top

app = FastAPI(title="Analyst-in-the-Loop SQL Agent API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
    request_id = str(uuid.uuid4())[:8] # Create a short unique ID
    print(f"\n>>> STARTING REQUEST [{request_id}] for: {request.message}\n")
    
    try:
        initial_state = {
            "messages": [HumanMessage(content=request.message)],
            "sql_query": "",
            "agent_reply": "",
            "error": "",
            "data": {},
            "retry_count": 0
        }
        
        final_state = agent_app.invoke(initial_state) 
        
        print(f"\n<<< FINISHED REQUEST [{request_id}]\n")
        
        return {
            "reply": final_state.get("agent_reply", ""),
            "sql_generated": final_state.get("sql_query", ""),
            "data_result": final_state.get("data", {})
        }
    except Exception as e:
        print(f"!!! ERROR IN REQUEST [{request_id}]: {e}")
        raise HTTPException(status_code=500, detail=str(e))