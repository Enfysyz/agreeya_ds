## Install Ollama model
```bash
docker exec -it malis_ollama ollama pull llama3
```

## View Db
```bash
docker exec -it malis_db psql -U user -d logistics
```
## Business Logic

The pipeline evaluates requests sequentially across four distinct AI agents:

- Fraud Agent: Analyzes the shipment route, cost, and goods for risk (0-100 score).

- Funding Agent: Acts as the financial gatekeeper. It queries the customer_invoices database to calculate the customer's total unpaid balance and enforces strict credit limits based on the Fraud Agent's risk score ($5k max for moderate risk, $20k max for standard).

- Billing Agent: Dynamically generates an invoice (including 8% tax) and assigns payment terms (e.g., Net 15 vs. Net 30).

- Compliance Agent: Validates the final transaction against strict regulatory rules (e.g., hazardous materials, correct tax math).

## Endpoints

### 1. Process Shipment (Synchronous)

Runs the full pipeline and returns the final result.

- **URL:** `/process-shipment`
- **Method:** `POST`
- **Content-Type:** `application/json`

#### Request Body

```json
{
  "shipment": {
    "customer_id": "CUST-9921",
    "route": "Los Angeles, CA -> Dallas, TX",
    "cost": 4500.00,
    "goods_description": "High-value electronics, laptops and servers."
  }
}
```

#### Response (200 OK)

```json
{
  "message": "Shipment processed successfully",
  "transaction_id": "uuid",
  "final_state": {
    "shipment": {},
    "fraud_score": 85,
    "fraud_reasoning": "High-value electronics carry severe risk.",
    "funding_decision": "Rejected",
    "funding_terms": "High fraud risk.",
    "invoice_details": {
      "status": "Cancelled",
      "total": 0
    },
    "compliance_status": "Rejected",
    "compliance_notes": "Halted due to prior agent rejection."
  }
}
```

---

### 2. Stream Shipment (Server-Sent Events)

Streams pipeline execution in real time. Each event represents a completed step.

- **URL:** `/stream-shipment`
- **Method:** `POST`
- **Content-Type:** `application/json`
- **Accept:** `text/event-stream`

#### Request Body

Same as `/process-shipment`.

#### Stream Response Example

```text
data: {"agent": "fraud", "state_update": {"fraud_score": 15, "fraud_reasoning": "Standard shipment, low risk."}}

data: {"agent": "funding", "state_update": {"funding_decision": "Approved", "funding_terms": "Net 30, Standard limits."}}

data: {"agent": "billing", "state_update": {"invoice_details": {"status": "Generated", "base_cost": 4500.0, "tax": 360.0, "total": 4860.0}}}

data: {"agent": "compliance", "state_update": {"compliance_status": "Approved", "compliance_notes": "All regulatory checks passed."}}

data: {"agent": "system", "status": "complete", "transaction_id": "uuid"}
```

---

### 3. Get Shipment History

Retrieves a previously processed shipment using its transaction ID.

- **URL:** `/shipment/{transaction_id}`
- **Method:** `GET`

#### Path Parameters

- `transaction_id` (string): Unique identifier for the shipment.

#### Response (200 OK)

```json
{
  "transaction_id": "uuid",
  "status": "Completed",
  "data": {
    "shipment": {
      "customer_id": "CUST-9921",
      "route": "Los Angeles, CA -> Dallas, TX",
      "cost": 4500.0,
      "goods_description": "High-value electronics"
    },
    "fraud_score": 15,
    "fraud_reasoning": "Standard shipment, low risk.",
    "funding_decision": "Approved",
    "funding_terms": "Net 30, Standard limits.",
    "invoice_details": {
      "status": "Generated",
      "base_cost": 4500.0,
      "tax": 360.0,
      "total": 4860.0
    },
    "compliance_status": "Approved",
    "compliance_notes": "All regulatory checks passed."
  }
}
```

#### Error (404 Not Found)

```json
{
  "detail": "Transaction not found"
}
```

---

## Notes

- All requests and responses use JSON unless otherwise specified.
- Streaming endpoint uses Server-Sent Events (SSE).
- Data is persisted using PostgreSQL with LangGraph checkpointing.