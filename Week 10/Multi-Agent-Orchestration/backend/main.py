from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import json
from graph import app_graph

app = FastAPI(title="Multi-Agent Company Intelligence API")

class ResearchRequest(BaseModel):
    company: str

@app.post("/analyze")
async def analyze_company(request: ResearchRequest):
    """Trigger the LangGraph workflow and stream the agent outputs via SSE."""
    
    async def event_generator():
        initial_state = {
            "company": request.company,
            "data_iterations": 0,
            "report_iterations": 0
        }
        
        try:
            # .astream() yields events as each node in the graph finishes
            async for event in app_graph.astream(initial_state):
                
                # 'event' is a dict containing the node name and the state it updated
                # Example: {"research_company": {"company_data": {...}}}
                for node_name, node_output in event.items():
                    
                    # Package it nicely for the frontend
                    payload = {
                        "agent": node_name,
                        "status": "completed",
                        "data": node_output
                    }
                    
                    # Yield in strict SSE format (data: <json>\n\n)
                    yield f"data: {json.dumps(payload)}\n\n"
                    
            # Send a final termination event when the graph finishes
            yield f"data: {json.dumps({'agent': 'system', 'status': 'done'})}\n\n"
            
        except Exception as e:
            error_payload = {"agent": "system", "status": "error", "message": str(e)}
            yield f"data: {json.dumps(error_payload)}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")