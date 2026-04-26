import logging
from langgraph.graph import StateGraph, START, END
from src.state import AgentState

# Import agents
from src.agents.researchers.company import research_company
from src.agents.researchers.competitor import research_competitor
from src.agents.researchers.market import research_market
from src.agents.researchers.financial import research_financial
from src.agents.evaluators.validator import validate_data
from src.agents.writer import write_report
from src.agents.evaluators.critic import critique_report

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
workflow.add_node("validate_data", validate_data)
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
