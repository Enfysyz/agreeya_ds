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
    report: str
    critic_issues: list
    critic_improvements: list
    score: int
    iterations: int

def extract_json(response_content: str, agent_name: str) -> dict:
    try:
        return json.loads(response_content)
    except json.JSONDecodeError as e:
        logging.error(f"[{agent_name}] JSON decoding failed: {e}")
        return {"error": "Failed to extract valid data"}

# --- ASYNC RESEARCH AGENTS ---

async def research_company(state: AgentState):
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
    response = await llm.ainvoke(prompt) # Async invoke
    data = extract_json(response.content, "CompanyAgent")
    return {"company_data": data}

async def research_competitor(state: AgentState):
    logging.info(f"⚔️ Starting Competitor Research for: {state['company']}")
    prompt = f"""You are a competitive intelligence strategist. Analyze the competitors for {state['company']}.
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
    prompt = f"""You are an expert industry analyst. Analyze the broader market for {state['company']}.
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
    prompt = f"""You are a corporate financial analyst. Estimate and summarize the financials for {state['company']}.
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

# --- ASYNC SYNTHESIS & QA AGENTS ---

async def write_report(state: AgentState):
    iters = state.get("iterations", 0) + 1
    logging.info(f"✍️ Compiling Final Report (Iteration {iters})...")
    
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
    report = await writer_llm.ainvoke(prompt) # Async invoke
    return {"report": report.content, "iterations": iters}

async def critique_report(state: AgentState):
    logging.info("🧪 Critic Agent is reviewing the report...")
    prompt = f"""You are a ruthless Senior Partner at a top consulting firm. Review this draft business report for {state['company']}.
    
    Here is the RAW DATA the Writer was given to work with:
    Company Data: {json.dumps(state.get('company_data', {}))}
    Market Data: {json.dumps(state.get('market_data', {}))}
    Financial Data: {json.dumps(state.get('financial_data', {}))}
    
    Report Draft:
    {state['report']}
    
    CRITICAL INSTRUCTION: DO NOT penalize the report for missing specific numbers, metrics, or data points IF those points are not present in the RAW DATA. Evaluate the report strictly on:
    1. How well it synthesized the provided data.
    2. The absence of redundancy.
    3. The logical strength and actionability of the Strategic Recommendations based on the available facts.
    
    You MUST respond with a JSON object using exactly these keys:
    - "score": An integer between 1 and 10.
    - "issues": A list of specific strings detailing structural or logical flaws.
    - "improvements": A list of actionable instructions for the next draft.
    """
    
    response = await llm.ainvoke(prompt) # Async invoke
    data = extract_json(response.content, "CriticAgent")
    
    score = data.get("score", 5)
    issues = data.get("issues", ["Failed to parse specific issues."])
    improvements = data.get("improvements", ["Improve overall depth and structure."])
    
    return {"score": score, "critic_issues": issues, "critic_improvements": improvements}

def check_quality(state: AgentState):
    if state["score"] >= 8 or state["iterations"] >= 3:
        return "end"
    else:
        return "rewrite"

# --- BUILD GRAPH ---
workflow = StateGraph(AgentState)

workflow.add_node("research_company", research_company)
workflow.add_node("research_competitor", research_competitor)
workflow.add_node("research_market", research_market)
workflow.add_node("research_financial", research_financial)
workflow.add_node("write_report", write_report)
workflow.add_node("critique_report", critique_report)

workflow.add_edge(START, "research_company")
workflow.add_edge(START, "research_competitor")
workflow.add_edge(START, "research_market")
workflow.add_edge(START, "research_financial")

workflow.add_edge(["research_company", "research_competitor", "research_market", "research_financial"], "write_report")
workflow.add_edge("write_report", "critique_report")
workflow.add_conditional_edges("critique_report", check_quality, {"end": END, "rewrite": "write_report"})

app_graph = workflow.compile()