import json
import os
import logging
from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from langchain_ollama import ChatOllama

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(levelname)s] - %(message)s",
    datefmt="%H:%M:%S"
)

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

llm = ChatOllama(
    model="llama3", 
    temperature=0, 
    base_url=OLLAMA_BASE_URL, 
    format="json"
)

writer_llm = ChatOllama(
    model="llama3", 
    temperature=0.4,
    base_url=OLLAMA_BASE_URL
)

class AgentState(TypedDict):
    company: str
    company_data: dict
    competitor_data: dict
    market_data: dict
    financial_data: dict
    
    # Data Validation Phase
    data_iterations: int
    missing_data_targets: list[str]
    research_feedback: dict
    
    # Report Phase
    report: str
    report_iterations: int
    report_score: int
    report_feedback: str

def extract_json(response_content: str, agent_name: str) -> dict:
    try:
        return json.loads(response_content)
    except json.JSONDecodeError as e:
        logging.error(f"[{agent_name}] JSON decoding failed: {e}")
        return {"error": "Failed to extract valid data"}

# --- ASYNC RESEARCH AGENTS ---

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

# --- ASYNC SYNTHESIS & QA AGENTS ---
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

def route_data(state: AgentState) -> list[str]:
    targets = state.get("missing_data_targets", [])
    if len(targets) > 0 and state.get("data_iterations", 0) < 3:
        logging.warning(f"🔄 Triggering re-research. Waking up all agents, but only these will execute: {targets}")
        
        # ALWAYS spawn all 4 to prevent LangGraph fan-in deadlocks
        return ["research_company", "research_competitor", "research_market", "research_financial"]
    
    logging.info("✅ Data Approved! Moving to Synthesis.")
    return ["write_report"]

def route_report(state: AgentState):
    if state.get("report_score", 0) >= 8 or state.get("report_iterations", 0) >= 3:
        logging.info("🎉 Final Report Approved!")
        return END
    
    logging.warning("♻️ Report needs edits. Sending back to Writer.")
    return "write_report"

# --- BUILD GRAPH ---
workflow = StateGraph(AgentState)

workflow.add_node("research_company", research_company)
workflow.add_node("research_competitor", research_competitor)
workflow.add_node("research_market", research_market)
workflow.add_node("research_financial", research_financial)
workflow.add_node("validate_data", validate_data) # NEW NODE
workflow.add_node("write_report", write_report)
workflow.add_node("critique_report", critique_report)

# 1. Parallel start
workflow.add_edge(START, "research_company")
workflow.add_edge(START, "research_competitor")
workflow.add_edge(START, "research_market")
workflow.add_edge(START, "research_financial")

# 2. All researchers report to the Data Validator
workflow.add_edge(["research_company", "research_competitor", "research_market", "research_financial"], "validate_data")

# 3. Data Validator Routing
workflow.add_conditional_edges(
    "validate_data", 
    route_data, 
    ["write_report", "research_company", "research_competitor", "research_market", "research_financial"]
)

# 4. Writer to Editor loop
workflow.add_edge("write_report", "critique_report")
workflow.add_conditional_edges(
    "critique_report", 
    route_report, 
    {END: END, "write_report": "write_report"}
)

app_graph = workflow.compile()