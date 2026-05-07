import os
import uuid
import json
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from psycopg_pool import ConnectionPool
from langgraph.checkpoint.postgres import PostgresSaver

from app.schema import ShipmentRequest
from app.workflow import build_logistics_graph

DB_URI = os.getenv("DATABASE_URL", "postgresql://user:password@db:5432/logistics")

logistics_pipeline = None
db_pool = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global logistics_pipeline, db_pool
    db_pool = ConnectionPool(conninfo=DB_URI, max_size=10, kwargs={"autocommit": True})
    checkpointer = PostgresSaver(db_pool)
    checkpointer.setup()
    logistics_pipeline = build_logistics_graph(checkpointer=checkpointer)
    yield
    db_pool.close()

app = FastAPI(title="Multi-Agent Logistics Intelligence API", lifespan=lifespan)

@app.post("/process-shipment")
async def process_shipment(request: ShipmentRequest):
    try:
        # Generate a unique thread ID for this specific transaction
        thread_id = str(uuid.uuid4())
        
        # Configure LangGraph with this thread_id to persist state correctly
        config = {"configurable": {"thread_id": thread_id}}
        
        # Initialize the graph state
        initial_state = {
            "shipment": request.shipment.model_dump(),
            "fraud_score": None,
            "fraud_reasoning": None,
            "funding_decision": None,
            "funding_terms": None,
            "invoice_details": None,
            "compliance_status": None,
            "compliance_notes": None
        }
        
        # Execute the pipeline. The checkpointer automatically saves state at every node.
        final_state = logistics_pipeline.invoke(initial_state, config=config)
        
        return {
            "message": "Shipment processed successfully",
            "transaction_id": thread_id,  # Return the ID so the frontend can query it later
            "final_state": final_state
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# NEW: Server-Sent Events Endpoint
@app.post("/stream-shipment")
async def stream_shipment(request: ShipmentRequest):
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    
    initial_state = {
        "shipment": request.shipment.model_dump(),
        "fraud_score": None, "fraud_reasoning": None,
        "funding_decision": None, "funding_terms": None,
        "invoice_details": None,
        "compliance_status": None, "compliance_notes": None
    }

    async def event_generator():
        try:
            # LangGraph's .stream() yields an update every time a node finishes
            for output in logistics_pipeline.stream(initial_state, config=config):
                # Output looks like: {"fraud": {"fraud_score": 85, ...}}
                for node_name, state_update in output.items():
                    
                    # Package the data for the frontend
                    payload = {
                        "agent": node_name,
                        "state_update": state_update
                    }
                    
                    # SSE requires this specific string format: "data: {json}\n\n"
                    yield f"data: {json.dumps(payload)}\n\n"
                    
                    # Small sleep to ensure the buffer flushes to the client immediately
                    await asyncio.sleep(0.05) 
            
            # Send a final completion event with the thread_id
            yield f"data: {json.dumps({'agent': 'system', 'status': 'complete', 'transaction_id': thread_id})}\n\n"
            
        except Exception as e:
             yield f"data: {json.dumps({'agent': 'system', 'error': str(e)})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

@app.get("/shipment/{transaction_id}")
async def get_shipment_status(transaction_id: str):
    try:
        # Configure the thread_id we want to look up
        config = {"configurable": {"thread_id": transaction_id}}
        
        # Query the LangGraph Postgres Checkpointer
        state_snapshot = logistics_pipeline.get_state(config)
        
        # If the state values are empty, the ID doesn't exist
        if not state_snapshot or not state_snapshot.values:
            raise HTTPException(status_code=404, detail="Transaction not found")
            
        return {
            "transaction_id": transaction_id,
            "status": "Completed" if not state_snapshot.next else "In Progress",
            "data": state_snapshot.values
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
