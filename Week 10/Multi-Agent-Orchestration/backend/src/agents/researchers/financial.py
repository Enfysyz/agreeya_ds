import logging
from src.state import AgentState
from src.llm import llm
from src.utils import extract_json

async def research_financial(state: AgentState):
    logging.info(f"💰 Starting Financial Research for: {state['company']}")

    if state.get("data_iterations", 0) > 0 and "research_financial" not in state.get("missing_data_targets", []):
        logging.info("⏭️ Financial Agent skipping (Data already valid).")
        return {} # Do not update state, preserve existing data

    # Inject Critic's research gaps if this is a second attempt
    # Extract ONLY the feedback meant for this specific agent
    agent_feedback = state.get("research_feedback", {}).get("research_financial", "")
    
    gap_instruction = ""
    if state.get("data_iterations", 0) > 0 and agent_feedback:
        gap_instruction = f"""
        CRITICAL FEEDBACK FROM PREVIOUS ATTEMPT:
        The previous data you gathered was insufficient. Specifically: {agent_feedback}
        You MUST dig deeper and address these specific gaps in this iteration.
        """

    prompt = f"""You are a corporate financial analyst. Estimate and summarize the financials for {state['company']}.
    {gap_instruction}
    If exact public data is unavailable, provide highly educated industry estimates. 
    You MUST respond with a JSON object using exactly these keys:
    - "revenue": Estimated annual revenue or revenue scale.
    - "profitability": Current profitability status or margin profile.
    - "funding": Known funding rounds, public market status, or capital structure.
    - "key_metrics": A list of the most important financial KPIs for this specific business model.
    - "financial_risks": A list of potential financial headwinds.
    """
    response = await llm.ainvoke(prompt)
    data = extract_json(response.content, "FinancialAgent")
    return {"financial_data": data}
