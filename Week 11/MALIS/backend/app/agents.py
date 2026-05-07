import os
from pydantic import BaseModel, Field
from langchain_community.chat_models import ChatOllama
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import PydanticOutputParser, StrOutputParser
from app.schema import WorkflowState
import json

# 1. Define the exact schema
class FraudAnalysis(BaseModel):
    score: int = Field(description="Fraud risk score from 0 to 100. Higher means more risk.")
    reason: str = Field(description="A concise, one-sentence explanation for the assigned score.")

OLLAMA_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

# 2. Initialize the LLM with format="json"
# This is crucial: it forces the Ollama engine to strictly generate valid JSON syntax.
llm = ChatOllama(
    base_url=OLLAMA_URL, 
    model="llama3", 
    temperature=0.1, 
    format="json"
)

# 3. Set up the Pydantic parser
parser = PydanticOutputParser(pydantic_object=FraudAnalysis)

def fraud_detection_node(state: WorkflowState) -> WorkflowState:
    shipment = state["shipment"]
    
    # We add an explicit instruction to avoid the 'properties' wrapper
    prompt = PromptTemplate(
        template=(
            "Analyze this shipment for fraud risk.\n"
            "Shipment details: {shipment}\n\n"
            "{format_instructions}\n"
            "IMPORTANT: Return ONLY a flat JSON object. Do not wrap your response in a 'properties' key. Start directly with {{'score': ...}}"
        ),
        input_variables=["shipment"],
        partial_variables={"format_instructions": parser.get_format_instructions()},
    )
    
    # Pipe to StrOutputParser to isolate the raw text from the LLM
    chain = prompt | llm | StrOutputParser()
    
    try:
        raw_output = chain.invoke({"shipment": shipment})
        print(f"\n--- DEBUG: Raw LLM Output ---\n{raw_output}\n---------------------------\n")
        
        # 1. Clean markdown if the LLM added it (e.g., ```json ... ```)
        cleaned_output = raw_output.strip()
        if cleaned_output.startswith("```json"):
            cleaned_output = cleaned_output[7:]
        if cleaned_output.endswith("```"):
            cleaned_output = cleaned_output[:-3]
        cleaned_output = cleaned_output.strip()

        # 2. Parse the string into a Python dictionary natively
        output_dict = json.loads(cleaned_output)
        
        # 3. The Unwrapper: If Mistral STILL wrapped it in "properties", strip it out!
        if "properties" in output_dict and isinstance(output_dict["properties"], dict):
            output_dict = output_dict["properties"]
            
        # 4. Instantiate the Pydantic model directly using kwargs unpacking
        # (This completely bypasses LangChain's crash-prone parser)
        result = FraudAnalysis(**output_dict)
        
        score = result.score
        reason = result.reason
        
    except json.JSONDecodeError:
        print("Agent Parsing Error: Output was not valid JSON.")
        score = 50
        reason = "System fallback: LLM failed to output valid JSON syntax."
    except Exception as e:
        print(f"Agent Validation Error: {e}")
        score = 50
        reason = "System fallback: LLM output did not match expected schema."

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