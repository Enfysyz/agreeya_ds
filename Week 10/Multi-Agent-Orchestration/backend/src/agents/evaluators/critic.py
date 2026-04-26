import logging
from src.state import AgentState
from src.llm import llm
from src.utils import extract_json

async def critique_report(state: AgentState):
    logging.info("🧪 Report Editor reviewing the draft...")
    
    prompt = f"""You are an Executive Editor. Review this report draft for {state['company']}.
    Draft: {state['report']}
    
    Grade ONLY the writing quality, synthesis, flow, and absence of redundancy.
    
    You MUST respond with a JSON object using exactly these keys:
    - "score": integer 1-10
    - "feedback": "Actionable instructions for the next draft."
    """
    response = await llm.ainvoke(prompt)
    data = extract_json(response.content, "ReportCritic")
    
    return {
        "report_score": data.get("score", 5),
        "report_feedback": data.get("feedback", "Improve synthesis and flow.")
    }
