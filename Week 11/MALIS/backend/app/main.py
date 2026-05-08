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
    
    # --- NEW: Create our custom business data table ---
    with db_pool.connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS customer_invoices (
                transaction_id TEXT PRIMARY KEY,
                customer_id TEXT,
                total_amount NUMERIC,
                payment_status TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
    
    checkpointer = PostgresSaver(db_pool)
    checkpointer.setup()
    logistics_pipeline = build_logistics_graph(checkpointer=checkpointer)
    yield
    db_pool.close()

app = FastAPI(title="Multi-Agent Logistics Intelligence API", lifespan=lifespan)

# --- HELPER FUNCTION FOR DB READ/WRITE ---
def get_customer_balance(customer_id: str) -> float:
    """Queries the database to find the total unpaid balance for a customer."""
    with db_pool.connection() as conn:
        result = conn.execute(
            "SELECT COALESCE(SUM(total_amount), 0) FROM customer_invoices WHERE customer_id = %s AND payment_status = 'Unpaid'",
            (customer_id,)
        ).fetchone()
        return float(result[0])

def save_approved_invoice(thread_id: str, customer_id: str, invoice: dict, compliance_status: str):
    """Saves the final invoice to the database ONLY if the system approved it."""
    if invoice and invoice.get("status") == "Generated" and compliance_status == "Approved":
        with db_pool.connection() as conn:
            conn.execute(
                """
                INSERT INTO customer_invoices (transaction_id, customer_id, total_amount, payment_status)
                VALUES (%s, %s, %s, 'Unpaid')
                ON CONFLICT (transaction_id) DO NOTHING;
                """,
                (thread_id, customer_id, invoice.get("total", 0))
            )

# --- ENDPOINTS ---

@app.post("/process-shipment")
async def process_shipment(request: ShipmentRequest):
    try:
        thread_id = str(uuid.uuid4())
        config = {"configurable": {"thread_id": thread_id}}
        
        # 1. THE READ: Get the historical balance before starting the agents
        current_balance = get_customer_balance(request.shipment.customer_id)
        
        initial_state = {
            "shipment": request.shipment.model_dump(),
            "customer_outstanding_balance": current_balance, # <-- Injected here
            "fraud_score": None, "fraud_reasoning": None,
            "funding_decision": None, "funding_terms": None,
            "invoice_details": None,
            "compliance_status": None, "compliance_notes": None
        }
        
        final_state = logistics_pipeline.invoke(initial_state, config=config)
        
        # 2. THE WRITE: Save the invoice if the pipeline was successful
        save_approved_invoice(
            thread_id=thread_id,
            customer_id=request.shipment.customer_id,
            invoice=final_state.get("invoice_details", {}),
            compliance_status=final_state.get("compliance_status")
        )
        
        return {
            "message": "Shipment processed successfully",
            "transaction_id": thread_id,
            "current_unpaid_balance": current_balance + final_state.get("invoice_details", {}).get("total", 0),
            "final_state": final_state
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/stream-shipment")
async def stream_shipment(request: ShipmentRequest):
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    
    # 1. THE READ: Get the historical balance
    current_balance = get_customer_balance(request.shipment.customer_id)
    
    initial_state = {
        "shipment": request.shipment.model_dump(),
        "customer_outstanding_balance": current_balance, # <-- Injected here
        "fraud_score": None, "fraud_reasoning": None,
        "funding_decision": None, "funding_terms": None,
        "invoice_details": None,
        "compliance_status": None, "compliance_notes": None
    }

    async def event_generator():
        final_state_tracker = {}
        try:
            for output in logistics_pipeline.stream(initial_state, config=config):
                for node_name, state_update in output.items():
                    # Keep track of the state as it streams to save it at the end
                    final_state_tracker.update(state_update)
                    
                    payload = {"agent": node_name, "state_update": state_update}
                    yield f"data: {json.dumps(payload)}\n\n"
                    await asyncio.sleep(0.05) 
            
            # 2. THE WRITE: Save the invoice after the stream finishes
            save_approved_invoice(
                thread_id=thread_id,
                customer_id=request.shipment.customer_id,
                invoice=final_state_tracker.get("invoice_details", {}),
                compliance_status=final_state_tracker.get("compliance_status")
            )
            
            yield f"data: {json.dumps({'agent': 'system', 'status': 'complete', 'transaction_id': thread_id})}\n\n"
            
        except Exception as e:
             yield f"data: {json.dumps({'agent': 'system', 'error': str(e)})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

@app.get("/shipment/{transaction_id}")
async def get_shipment_status(transaction_id: str):
    # (Keep your existing GET endpoint exactly the same)
    try:
        config = {"configurable": {"thread_id": transaction_id}}
        state_snapshot = logistics_pipeline.get_state(config)
        
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