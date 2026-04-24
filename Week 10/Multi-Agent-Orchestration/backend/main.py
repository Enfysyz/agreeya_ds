from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from graph import app_graph

app = FastAPI(title="Multi-Agent Company Intelligence API")

class ResearchRequest(BaseModel):
    company: str

@app.post("/analyze")
async def analyze_company(request: ResearchRequest):
    """Trigger the LangGraph workflow."""
    try:
        # Initialize the state
        initial_state = {
            "company": request.company,
            "iterations": 0
        }
        
        # Run the graph
        result = app_graph.invoke(initial_state)
        
        return {
            "company": result.get("company"),
            "final_score": result.get("score"),
            "iterations_taken": result.get("iterations"),
            "report": result.get("report")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))