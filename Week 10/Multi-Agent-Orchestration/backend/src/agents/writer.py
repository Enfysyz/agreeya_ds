import logging
import json
from src.state import AgentState
from src.llm import writer_llm

async def write_report(state: AgentState):
    iters = state.get("report_iterations", 0) + 1
    logging.info(f"✍️ Compiling Final Report (Iteration {iters})...")
    
    feedback_context = ""
    if iters > 1:
        feedback_context = f"CRITICAL EDITOR FEEDBACK: {state.get('report_feedback')}. Fix this in the new draft."

    prompt = f"""You are a Senior Consultant. Synthesize this data into a professional report for {state['company']}.
    {feedback_context}
    
    Company Data: {json.dumps(state.get('company_data', {}))}
    Competitor Data: {json.dumps(state.get('competitor_data', {}))}
    Market Data: {json.dumps(state.get('market_data', {}))}
    Financial Data: {json.dumps(state.get('financial_data', {}))}
    """
    report = await writer_llm.ainvoke(prompt)
    return {"report": report.content, "report_iterations": iters}
