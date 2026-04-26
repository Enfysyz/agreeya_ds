from typing import TypedDict, List, Dict, Any

class AgentState(TypedDict):
    company: str
    company_data: Dict[str, Any]
    competitor_data: Dict[str, Any]
    market_data: Dict[str, Any]
    financial_data: Dict[str, Any]
    
    # Data Validation Phase
    data_iterations: int
    missing_data_targets: List[str]
    research_feedback: Dict[str, Any]
    
    # Report Phase
    report: str
    report_iterations: int
    report_score: int
    report_feedback: str
