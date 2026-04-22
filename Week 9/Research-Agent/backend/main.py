from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from agent import ResearchAgent

app = FastAPI(title="Deep Research AI Agent")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define the expected JSON payload
class ResearchRequest(BaseModel):
    topic: str

@app.post("/api/research")
async def research_endpoint(request: ResearchRequest):
    agent = ResearchAgent()
    
    # Return an HTTP response that stays open and streams the yields from the agent
    return StreamingResponse(
        agent.run_research(request.topic),
        media_type="text/event-stream"
    )