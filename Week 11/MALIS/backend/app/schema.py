from typing import TypedDict, Optional
from pydantic import BaseModel

class ShipmentDetails(BaseModel):
    customer_id: str
    route: str
    cost: float
    goods_description: str

class ShipmentRequest(BaseModel):
    shipment: ShipmentDetails

class WorkflowState(TypedDict):
    shipment: dict
    fraud_score: Optional[int]
    fraud_reasoning: Optional[str]
    funding_decision: Optional[str]
    funding_terms: Optional[str]
    invoice_details: Optional[dict]
    compliance_status: Optional[str]
    compliance_notes: Optional[str]