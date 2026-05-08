from typing import TypedDict, Optional, Literal
from pydantic import BaseModel, Field

class ShipmentDetails(BaseModel):
    customer_id: str
    route: str
    cost: float
    goods_description: str

class ShipmentRequest(BaseModel):
    shipment: ShipmentDetails

class ComplianceAnalysis(BaseModel):
    status: Literal["Approved", "Flagged", "Rejected"] = Field(
        description="The final decision based on regulatory checks."
    )
    reason: str = Field(
        description="A clear, single-sentence explanation of why the status was chosen."
    )

class WorkflowState(TypedDict):
    shipment: dict
    customer_outstanding_balance: float
    fraud_score: Optional[int]
    fraud_reasoning: Optional[str]
    funding_decision: Optional[str]
    funding_terms: Optional[str]
    invoice_details: Optional[dict]
    compliance_status: Optional[str]
    compliance_notes: Optional[str]