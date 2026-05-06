import os
import uuid
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from psycopg_pool import ConnectionPool
from langgraph.checkpoint.postgres import PostgresSaver

from app.schema import ShipmentRequest
from app.workflow import build_logistics_graph

DB_URI = os.getenv("DATABASE_URL", "postgresql://user:password@db:5432/logistics")

# Global variables to hold the pipeline and database pool
logistics_pipeline = None
db_pool = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global logistics_pipeline, db_pool
    
    # 1. Initialize Postgres connection pool
    db_pool = ConnectionPool(
        conninfo=DB_URI, 
        max_size=10,
        kwargs={"autocommit": True}  # <-- THIS IS THE FIX
    )
    
    # 2. Setup the LangGraph Postgres checkpointer
    checkpointer = PostgresSaver(db_pool)
    
    # 3. Automatically create the required state-tracking tables in PostgreSQL
    checkpointer.setup()
    
    # 4. Compile the graph with the checkpointer
    logistics_pipeline = build_logistics_graph(checkpointer=checkpointer)
    
    yield  # Let the FastAPI app run
    
    # 5. Clean up the connection pool on shutdown
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