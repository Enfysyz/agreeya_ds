import logging
import json
from src.state import AgentState
from src.llm import llm
from src.utils import extract_json

async def validate_data(state: AgentState):
    iters = state.get("data_iterations", 0) + 1
    logging.info(f"🔎 Data Validator checking raw research (Iteration {iters})...")
    
    prompt = f"""You are a ruthless Data QA Engineer. Review the gathered research for {state['company']}.
    
    Company Data: {json.dumps(state.get('company_data', {}))}
    Competitor Data: {json.dumps(state.get('competitor_data', {}))}
    Market Data: {json.dumps(state.get('market_data', {}))}
    Financial Data: {json.dumps(state.get('financial_data', {}))}
    
    EVALUATION CHECKLIST:
    - FINANCIALS: Are there hard numbers ($, %, multiples) for revenue, margins, or funding?
    - MARKET: Is there a concrete Total Addressable Market (TAM) size or numerical growth rate?
    - COMPETITORS: Are there specific, named competitors with clear, factual differentiators?
    - COMPANY: Are the business model and products concrete, or just marketing fluff?
    
    INSTRUCTIONS: 
    If the data is vague, uses words like "a lot" instead of actual numbers, or fails ANY part of the checklist, you MUST mark it "invalid". Do not be lenient.
    
    You MUST respond with a JSON object using exactly these keys IN THIS EXACT ORDER:
    - "reasoning": Write 1-2 sentences explaining your thought process against the checklist.
    - "validation_status": strictly "valid" or "invalid".
    - "feedback_summary": A brief summary of why it was approved or rejected.
    - "agent_feedback": A dictionary mapping the specific agent name to its specific instructions. Example: {{"research_financial": "Missing exact revenue numbers. Find them.", "research_market": "TAM is missing."}}. Leave as empty {{}} if valid.
    """
    
    response = await llm.ainvoke(prompt)
    
    # --- START DEBUG LOGGING ---
    logging.info(f"=== RAW LLM OUTPUT (DataValidator) ===")
    logging.info(response.content)
    logging.info(f"=======================================")
    # --- END DEBUG LOGGING ---
    
    data = extract_json(response.content, "DataValidator")
    
    if "error" in data:
        logging.error(f"❌ Data Validator returned malformed JSON: {response.content}")
        return {
            "missing_data_targets": ["research_company", "research_competitor", "research_market", "research_financial"],
            "research_feedback": {
                "research_financial": "System error on validation. Ensure hard numbers are present.",
                "research_market": "System error on validation. Ensure hard numbers are present."
            },
            "data_iterations": iters
        }
        
    status = data.get("validation_status", "invalid").strip().lower()
    agent_feedback_dict = data.get("agent_feedback", {})
    summary = data.get("feedback_summary", "No summary provided.")
    reasoning = data.get("reasoning", "")
    
    is_valid = (status == "valid")
    
    # Deriving targets directly from the dictionary keys!
    targets = list(agent_feedback_dict.keys())
    
    # Defensive programming: If invalid but forgot to map feedback, trigger all.
    if not is_valid and not targets:
        logging.warning("⚠️ Validator marked invalid but provided no specific agent feedback. Firing all agents.")
        targets = ["research_company", "research_competitor", "research_market", "research_financial"]
        agent_feedback_dict = {
            "research_company": "General lack of depth. Dig deeper.",
            "research_competitor": "General lack of depth. Dig deeper.",
            "research_market": "General lack of depth. Dig deeper.",
            "research_financial": "General lack of depth. Dig deeper."
        }
    
    if is_valid:
        logging.info(f"✅ Data Approved! Reason: {reasoning}")
    else:
        logging.warning(f"⚠️ Data Rejected! Reason: {reasoning}")
        logging.warning(f"🎯 Auto-Derived Targets: {targets}")
            
    return {
        "missing_data_targets": [] if is_valid else targets,
        "research_feedback": agent_feedback_dict if not is_valid else {},
        "data_iterations": iters
    }
