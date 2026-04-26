import logging
from src.state import AgentState
from src.llm import llm
from src.utils import extract_json

async def research_company(state: AgentState):
    logging.info(f"🔍 Starting Company Research for: {state['company']}")
    
    if state.get("data_iterations", 0) > 0 and "research_company" not in state.get("missing_data_targets", []):
        logging.info("⏭️ Company Agent skipping (Data already valid).")
        return {} # Do not update state, preserve existing data
    # Extract ONLY the feedback meant for this specific agent
    agent_feedback = state.get("research_feedback", {}).get("research_company", "")
    
    gap_instruction = ""
    if state.get("data_iterations", 0) > 0 and agent_feedback:
        gap_instruction = f"""
        CRITICAL FEEDBACK FROM PREVIOUS ATTEMPT:
        The previous data you gathered was insufficient. Specifically: {agent_feedback}
        You MUST dig deeper and address these specific gaps in this iteration.
        """

    prompt = f"""You are a top-tier business analyst. Research the company {state['company']}.
    {gap_instruction}
    
    You MUST respond with a JSON object using exactly these keys:
    - "overview": A brief summary of what the company does.
    - "business_model": How the company makes money.
    - "products": A list of their core products or services.
    - "target_market": Who their primary customers are.
    - "strengths": A list of their main competitive advantages.
    - "weaknesses": A list of their internal weaknesses or vulnerabilities.
    """
    response = await llm.ainvoke(prompt) # Async invoke
    data = extract_json(response.content, "CompanyAgent")
    return {"company_data": data}
