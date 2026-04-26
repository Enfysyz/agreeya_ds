import logging
from src.state import AgentState
from src.llm import llm
from src.utils import extract_json

async def research_competitor(state: AgentState):
    logging.info(f"⚔️ Starting Competitor Research for: {state['company']}")

    if state.get("data_iterations", 0) > 0 and "research_competitor" not in state.get("missing_data_targets", []):
        logging.info("⏭️ Competitor Agent skipping (Data already valid).")
        return {} # Do not update state, preserve existing data
    # Extract ONLY the feedback meant for this specific agent
    agent_feedback = state.get("research_feedback", {}).get("research_competitor", "")
    
    gap_instruction = ""
    if state.get("data_iterations", 0) > 0 and agent_feedback:
        gap_instruction = f"""
        CRITICAL FEEDBACK FROM PREVIOUS ATTEMPT:
        The previous data you gathered was insufficient. Specifically: {agent_feedback}
        You MUST dig deeper and address these specific gaps in this iteration.
        """

    prompt = f"""You are a competitive intelligence strategist. Analyze the competitors for {state['company']}.
    {gap_instruction}

    Make your analysis highly comparative. You MUST respond with a JSON object using exactly these keys:
    - "competitors": An array of objects, where each object contains "name", "positioning", "strengths" (list), and "weaknesses" (list).
    - "competitive_landscape": A summary of how crowded or consolidated the industry is.
    - "company_positioning": A critical explanation of how {state['company']} compares to these competitors.
    """
    response = await llm.ainvoke(prompt)
    data = extract_json(response.content, "CompetitorAgent")
    return {"competitor_data": data}
