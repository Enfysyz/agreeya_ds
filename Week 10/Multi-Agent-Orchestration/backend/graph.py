import json
import os
import logging
from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from langchain_ollama import ChatOllama

# Configure logging to track every step
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(levelname)s] - %(message)s",
    datefmt="%H:%M:%S"
)

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
# Using your exact configuration!
llm = ChatOllama(
    model="llama3", 
    temperature=0, 
    base_url=OLLAMA_BASE_URL, 
    format="json"
)

# We also need a standard LLM for the Writer Agent (since it writes a text report, not JSON)
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
    report: str
    critic_issues: list
    critic_improvements: list
    score: int
    iterations: int

# --- HELPER FUNCTION ---
def extract_json(response_content: str, agent_name: str) -> dict:
    """Simple JSON parser since format='json' guarantees clean output."""
    try:
        return json.loads(response_content)
    except json.JSONDecodeError as e:
        logging.error(f"[{agent_name}] JSON decoding failed: {e}")
        return {"error": "Failed to extract valid data"}

# --- RESEARCH AGENTS (PARALLEL) ---

def research_company(state: AgentState):
    logging.info(f"🔍 Starting Company Research for: {state['company']}")
    prompt = f"""You are a top-tier business analyst. Research the company {state['company']}.
    You MUST respond with a JSON object using exactly these keys:
    - "overview": A brief summary of what the company does.
    - "business_model": How the company makes money.
    - "products": A list of their core products or services.
    - "target_market": Who their primary customers are.
    - "strengths": A list of their main competitive advantages.
    - "weaknesses": A list of their internal weaknesses or vulnerabilities.
    """
    response = llm.invoke(prompt)
    data = extract_json(response.content, "CompanyAgent") # Use .content here
    logging.info(f"✅ Completed Company Research for: {state['company']}")
    return {"company_data": data}

def research_competitor(state: AgentState):
    logging.info(f"⚔️ Starting Competitor Research for: {state['company']}")
    prompt = f"""You are a competitive intelligence strategist. Analyze the competitors for {state['company']}.
    Make your analysis highly comparative. You MUST respond with a JSON object using exactly these keys:
    - "competitors": An array of objects, where each object contains "name", "positioning", "strengths" (list), and "weaknesses" (list).
    - "competitive_landscape": A summary of how crowded or consolidated the industry is.
    - "company_positioning": A critical explanation of how {state['company']} compares to these competitors.
    """
    response = llm.invoke(prompt)
    data = extract_json(response.content, "CompetitorAgent")
    logging.info(f"✅ Completed Competitor Research for: {state['company']}")
    return {"competitor_data": data}

def research_market(state: AgentState):
    logging.info(f"📈 Starting Market Research for: {state['company']}")
    prompt = f"""You are an expert industry analyst. Analyze the broader market for {state['company']}.
    You MUST respond with a JSON object using exactly these keys:
    - "industry_overview": The current state of the industry.
    - "market_size": Estimated current size of the addressable market.
    - "growth_rate": Estimated growth rate or CAGR.
    - "trends": A list of current industry trends.
    - "risks": A list of macro-level risks (e.g., regulatory, technological).
    - "opportunities": A list of untouched or growing opportunities in the space.
    """
    response = llm.invoke(prompt)
    data = extract_json(response.content, "MarketAgent")
    logging.info(f"✅ Completed Market Research for: {state['company']}")
    return {"market_data": data}

def research_financial(state: AgentState):
    logging.info(f"💰 Starting Financial Research for: {state['company']}")
    prompt = f"""You are a corporate financial analyst. Estimate and summarize the financials for {state['company']}.
    If exact public data is unavailable, provide highly educated industry estimates. 
    You MUST respond with a JSON object using exactly these keys:
    - "revenue": Estimated annual revenue or revenue scale.
    - "profitability": Current profitability status or margin profile.
    - "funding": Known funding rounds, public market status, or capital structure.
    - "key_metrics": A list of the most important financial KPIs for this specific business model.
    - "financial_risks": A list of potential financial headwinds.
    """
    response = llm.invoke(prompt)
    data = extract_json(response.content, "FinancialAgent")
    logging.info(f"✅ Completed Financial Research for: {state['company']}")
    return {"financial_data": data}

# --- SYNTHESIS & QA AGENTS ---

def write_report(state: AgentState):
    iters = state.get("iterations", 0) + 1
    logging.info(f"✍️ Compiling Final Report (Iteration {iters})...")
    
    # Inject Critic Feedback if this is a rewrite
    # Set up the feedback context if the Critic Agent sent it back for a rewrite
    feedback_context = ""
    if iters > 1:
        feedback_context = f"""
        CRITICAL FEEDBACK FROM SENIOR PARTNER TO INCORPORATE:
        Issues identified: {state.get('critic_issues')}
        Required Improvements: {state.get('critic_improvements')}
        You MUST fix these issues thoroughly in this new draft! Do not ignore this feedback.
        """

    prompt = f"""You are a Senior Management Consultant. Synthesize the provided research data into a cohesive, highly professional business report for {state['company']}.
    Combine the inputs, remove redundancies, ensure smooth transitions, and draw logical conclusions.
    
    {feedback_context}
    
    RAW DATA INPUTS:
    Company Data: {json.dumps(state.get('company_data', {}))}
    Competitor Data: {json.dumps(state.get('competitor_data', {}))}
    Market Data: {json.dumps(state.get('market_data', {}))}
    Financial Data: {json.dumps(state.get('financial_data', {}))}

    OUTPUT STRUCTURE REQUIRED:
    1. Executive Summary
    2. Company Overview
    3. Business Model
    4. Market & Industry Analysis
    5. Competitive Landscape
    6. Financial Overview
    7. Risks & Opportunities
    8. Strategic Recommendations
    """
    report = writer_llm.invoke(prompt)
    logging.info("✅ Report Draft Completed.")
    return {"report": report.content, "iterations": iters}

def critique_report(state: AgentState):
    logging.info("🧪 Critic Agent is reviewing the report...")
    prompt = f"""You are a ruthless Senior Partner at a top consulting firm. Review this draft business report for {state['company']}.
    
    Report Draft:
    {state['report']}
    
    Look for shallow analysis, missing metrics, redundancy, and weak or generic recommendations. Do not be overly polite.
    You MUST respond with a JSON object using exactly these keys:
    - "score": An integer between 1 and 10 rating the overall quality and depth of the report.
    - "issues": A list of specific strings detailing exactly what is wrong, shallow, or missing.
    - "improvements": A list of specific, actionable instructions on what the writer must add or change in the next draft.
    """
    
    response = llm.invoke(prompt)
    data = extract_json(response.content, "CriticAgent")
    
    score = data.get("score", 5)
    issues = data.get("issues", ["Failed to parse specific issues."])
    improvements = data.get("improvements", ["Improve overall depth and structure."])
    
    logging.info(f"⚖️ Critic Score: {score}/10. Issues found: {len(issues)}")
    return {"score": score, "critic_issues": issues, "critic_improvements": improvements}

def check_quality(state: AgentState):
    if state["score"] >= 8:
        logging.info("🎉 Report passed quality threshold! Publishing final version.")
        return "end"
    elif state["iterations"] >= 3:
        logging.warning("⚠️ Max iterations reached. Publishing current version despite lower score.")
        return "end"
    else:
        logging.info("♻️ Report failed quality check. Sending back to Writer Agent.")
        return "rewrite"

# --- BUILD GRAPH ---
workflow = StateGraph(AgentState)

workflow.add_node("research_company", research_company)
workflow.add_node("research_competitor", research_competitor)
workflow.add_node("research_market", research_market)
workflow.add_node("research_financial", research_financial)
workflow.add_node("write_report", write_report)
workflow.add_node("critique_report", critique_report)

# True Parallel Fan-Out: Connect START to all 4 research agents
workflow.add_edge(START, "research_company")
workflow.add_edge(START, "research_competitor")
workflow.add_edge(START, "research_market")
workflow.add_edge(START, "research_financial")

# Fan-In: All research agents flow into the writer
workflow.add_edge(["research_company", "research_competitor", "research_market", "research_financial"], "write_report")

# Writer to Critic
workflow.add_edge("write_report", "critique_report")

# Conditional Feedback Loop
workflow.add_conditional_edges(
    "critique_report",
    check_quality,
    {
        "end": END,
        "rewrite": "write_report"
    }
)

app_graph = workflow.compile()