import logging
from src.state import AgentState
from src.llm import llm
from src.utils import extract_json

async def research_market(state: AgentState):
    logging.info(f"📈 Starting Market Research for: {state['company']}")

    if state.get("data_iterations", 0) > 0 and "research_market" not in state.get("missing_data_targets", []):
        logging.info("⏭️ Market Agent skipping (Data already valid).")
        return {} # Do not update state, preserve existing data

    # Extract ONLY the feedback meant for this specific agent
    agent_feedback = state.get("research_feedback", {}).get("research_market", "")
    
    gap_instruction = ""
    if state.get("data_iterations", 0) > 0 and agent_feedback:
        gap_instruction = f"""
        CRITICAL FEEDBACK FROM PREVIOUS ATTEMPT:
        The previous data you gathered was insufficient. Specifically: {agent_feedback}
        You MUST dig deeper and address these specific gaps in this iteration.
        """

    prompt = f"""You are an expert industry analyst. Analyze the broader market for {state['company']}.
    {gap_instruction}
    You MUST respond with a JSON object using exactly these keys:
    - "industry_overview": The current state of the industry.
    - "market_size": Estimated current size of the addressable market.
    - "growth_rate": Estimated growth rate or CAGR.
    - "trends": A list of current industry trends.
    - "risks": A list of macro-level risks (e.g., regulatory, technological).
    - "opportunities": A list of untouched or growing opportunities in the space.
    """
    response = await llm.ainvoke(prompt)
    data = extract_json(response.content, "MarketAgent")
    return {"market_data": data}
