import os
from langchain_community.chat_models import ChatOllama
from langchain_core.prompts import PromptTemplate
from app.schema import WorkflowState

# Configure Ollama to point to the docker service
OLLAMA_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
llm = ChatOllama(base_url=OLLAMA_URL, model="llama3", temperature=0.1)

def fraud_detection_node(state: WorkflowState) -> WorkflowState:
    shipment = state["shipment"]
    
    prompt = PromptTemplate.from_template(
        "Analyze this shipment for fraud risk (0-100) and provide a 1 sentence reason. "
        "Shipment: {shipment}\nFormat: 'Score: [number]\nReason: [text]'"
    )
    chain = prompt | llm
    result = chain.invoke({"shipment": shipment}).content
    
    # In production, use structured output parsing. For now, simple string splitting.
    try:
        score_line, reason_line = result.split('\n', 1)
        score = int(score_line.replace("Score: ", "").strip())
        reason = reason_line.replace("Reason: ", "").strip()
    except Exception:
        score = 50
        reason = "Failed to parse LLM output."

    return {"fraud_score": score, "fraud_reasoning": reason}

def funding_node(state: WorkflowState) -> WorkflowState:
    score = state.get("fraud_score", 100)
    
    if score > 75:
        return {"funding_decision": "Rejected", "funding_terms": "High fraud risk."}
    elif score > 40:
        return {"funding_decision": "Approved with Limits", "funding_terms": "Net 15, Max $5k credit."}
    else:
        return {"funding_decision": "Approved", "funding_terms": "Net 30, Standard limits."}

def billing_node(state: WorkflowState) -> WorkflowState:
    shipment = state["shipment"]
    funding = state.get("funding_decision", "Rejected")
    
    if funding == "Rejected":
        invoice = {"status": "Cancelled", "total": 0}
    else:
        base_cost = shipment.get("cost", 0)
        tax = base_cost * 0.08 # 8% tax mock
        invoice = {"status": "Generated", "base_cost": base_cost, "tax": tax, "total": base_cost + tax}
        
    return {"invoice_details": invoice}

def compliance_node(state: WorkflowState) -> WorkflowState:
    invoice = state.get("invoice_details", {})
    
    if invoice.get("status") == "Cancelled":
        return {"compliance_status": "Rejected", "compliance_notes": "Halted due to funding rejection."}
    else:
        return {"compliance_status": "Approved", "compliance_notes": "All regulatory checks passed."}