import os
import json
from pydantic import BaseModel, Field
from langchain_community.chat_models import ChatOllama
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import PydanticOutputParser, StrOutputParser
from app.schema import WorkflowState, ComplianceAnalysis
from datetime import datetime, timedelta

class FraudAnalysis(BaseModel):
    score: int = Field(description="Fraud risk score from 0 to 100. Higher means more risk.")
    reason: str = Field(description="A concise, one-sentence explanation for the assigned score.")

OLLAMA_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

llm = ChatOllama(
    base_url=OLLAMA_URL, 
    model="llama3", 
    temperature=0.1, 
    format="json"
)

# Parsers for format instructions
fraud_parser = PydanticOutputParser(pydantic_object=FraudAnalysis)
compliance_parser = PydanticOutputParser(pydantic_object=ComplianceAnalysis)

# --- HELPER FUNCTION ---
def parse_llm_output(raw_output: str, pydantic_model: type[BaseModel], fallback_dict: dict) -> dict:
    """Safely extracts JSON from the LLM, strips markdown/properties, and validates it."""
    try:
        cleaned_output = raw_output.strip()
        if cleaned_output.startswith("```json"):
            cleaned_output = cleaned_output[7:]
        if cleaned_output.endswith("```"):
            cleaned_output = cleaned_output[:-3]
        cleaned_output = cleaned_output.strip()

        output_dict = json.loads(cleaned_output)
        
        if "properties" in output_dict and isinstance(output_dict["properties"], dict):
            output_dict = output_dict["properties"]
            
        validated_data = pydantic_model(**output_dict)
        return validated_data.model_dump()
    except Exception as e:
        print(f"Parsing error: {e}")
        return fallback_dict

# --- AGENT NODES ---

def fraud_detection_node(state: WorkflowState) -> WorkflowState:
    shipment = state["shipment"]
    
    prompt = PromptTemplate(
        template=(
            "Analyze this logistics shipment for fraud risk.\n"
            "Shipment details: {shipment}\n\n"
            "Rules for evaluation:\n"
            "1. Shipments with a cost > $10,000 have an inherently higher baseline risk.\n"
            "2. High-value electronics (like servers or laptops) combined with cross-border or long-distance routes carry severe risk.\n"
            "3. Vague goods descriptions (e.g., 'misc items', 'supplies') should spike the risk score.\n\n"
            "{format_instructions}\n"
            "IMPORTANT: Return ONLY a flat JSON object. Do not wrap your response in a 'properties' key."
        ),
        input_variables=["shipment"],
        partial_variables={"format_instructions": fraud_parser.get_format_instructions()},
    )
    
    raw_output = (prompt | llm | StrOutputParser()).invoke({"shipment": shipment})
    print(f"\n--- Fraud LLM Output ---\n{raw_output}\n------------------------\n")
    
    fallback = {"score": 50, "reason": "System fallback: LLM failed to output valid JSON syntax."}
    result = parse_llm_output(raw_output, FraudAnalysis, fallback)

    return {"fraud_score": result["score"], "fraud_reasoning": result["reason"]}

def funding_node(state: WorkflowState) -> WorkflowState:
    score = state.get("fraud_score", 100)
    cost = state["shipment"].get("cost", 0)
    current_balance = state.get("customer_outstanding_balance", 0)
    
    # Calculate the total exposure if we approve this new shipment
    projected_balance = current_balance + cost

    if score > 75:
        return {"funding_decision": "Rejected", "funding_terms": "High fraud risk."}
        
    elif score > 40:
        # Enforce the strict $5k limit for moderate-risk profiles
        if projected_balance > 5000:
            return {
                "funding_decision": "Rejected", 
                "funding_terms": f"Credit Limit Exceeded. Requested: ${cost}. Current Balance: ${current_balance}. Max: $5000."
            }
        return {"funding_decision": "Approved with Limits", "funding_terms": "Net 15, Max $5k credit."}
        
    else:
        # Standard profiles might have a higher implied limit, e.g., $20k
        if projected_balance > 20000:
            return {
                "funding_decision": "Rejected", 
                "funding_terms": "Standard Credit Limit ($20k) Exceeded."
            }
        return {"funding_decision": "Approved", "funding_terms": "Net 30, Standard limits."}

def billing_node(state: WorkflowState) -> WorkflowState:
    shipment = state["shipment"]
    funding = state.get("funding_decision", "Rejected")
    terms = state.get("funding_terms", "")
    
    if funding == "Rejected":
        invoice = {"status": "Cancelled", "total": 0, "due_date": None}
    else:
        base_cost = shipment.get("cost", 0)
        tax = base_cost * 0.08
        total_cost = base_cost + tax
        
        # Calculate due date based on the enforced terms
        days_to_pay = 15 if "Net 15" in terms else 30
        due_date = (datetime.now() + timedelta(days=days_to_pay)).strftime("%Y-%m-%d")
        
        invoice = {
            "status": "Generated", 
            "base_cost": base_cost, 
            "tax": tax, 
            "total": total_cost,
            "due_date": due_date # <-- The programmatic rule applied
        }
        
    return {"invoice_details": invoice}

def compliance_node(state: WorkflowState) -> WorkflowState:
    invoice = state.get("invoice_details", {})
    shipment = state["shipment"]
    
    if invoice.get("status") == "Cancelled":
         return {"compliance_status": "Rejected", "compliance_notes": "Halted due to prior agent rejection."}

    prompt = PromptTemplate(
        template=(
            "Act as a strict Regulatory Compliance Officer for a logistics pipeline.\n"
            "Evaluate this transaction:\n"
            "Shipment: {shipment}\n"
            "Invoice: {invoice}\n\n"
            "Rules for evaluation:\n"
            "1. Ensure the tax applied in the invoice is exactly 8% of the base cost. If the math is wrong, status must be 'Flagged'.\n"
            "2. If the shipment contains hazardous materials, weapons, or controlled substances, status must be 'Rejected'.\n"
            "3. If the shipment cost exceeds $8,000, it requires an extra audit review; status must be 'Flagged'.\n"
            "4. Otherwise, status should be 'Approved'.\n\n"
            "{format_instructions}\n"
            "IMPORTANT: Return ONLY a flat JSON object. Do not wrap your response in a 'properties' key."
        ),
        input_variables=["shipment", "invoice"],
        partial_variables={"format_instructions": compliance_parser.get_format_instructions()},
    )
    
    raw_output = (prompt | llm | StrOutputParser()).invoke({"shipment": shipment, "invoice": invoice})
    print(f"\n--- Compliance LLM Output ---\n{raw_output}\n---------------------------\n")

    fallback = {"status": "Flagged", "reason": "System fallback: Failed to parse compliance logic."}
    result = parse_llm_output(raw_output, ComplianceAnalysis, fallback)

    return {"compliance_status": result["status"], "compliance_notes": result["reason"]}