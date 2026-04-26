# Multi-Agent Orchestration Backend

This document details the Multi-Agent API and the various agents that compose the LangGraph workflow, including their specific roles and JSON outputs.

# Download Ollama model
```bash
docker exec -it ollama_multi_agent ollama pull llama3
```

## Agent States
```python
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
```
## API Endpoints

### `POST /analyze`
Triggers the multi-agent LangGraph workflow to perform deep research on a specified company.

**Request Body:**
```json
{
  "company": "string"
}
```

**Response:**
Returns a **Server-Sent Events (SSE)** stream (`text/event-stream`). Each event yields a JSON payload as nodes in the graph complete.

**Event Payload Format:**
```json
{
  "agent": "string", // Name of the agent (e.g., "research_company", "system")
  "status": "string", // "completed", "error", or "done"
  "data": { ... }, // The output data from the specific agent (if status is "completed")
  "message": "string" // Error message (if status is "error")
}
```

---

## Agents Overview

The system uses a state graph (LangGraph) consisting of Researcher Agents, Evaluator Agents, and a Writer Agent.

### 1. Researcher Agents

These agents run in parallel at the start of the workflow.

#### **Company Agent** (`research_company`)
- **Role:** Top-tier business analyst. Researches the company's core operations.
- **State Key Updated:** `company_data`
- **Output JSON:**
  ```json
  {
    "overview": "Brief summary of what the company does.",
    "business_model": "How the company makes money.",
    "products": ["List of core products or services"],
    "target_market": "Primary customers.",
    "strengths": ["List of competitive advantages"],
    "weaknesses": ["List of internal vulnerabilities"]
  }
  ```

#### **Competitor Agent** (`research_competitor`)
- **Role:** Competitive intelligence strategist. Analyzes the company's competitors.
- **State Key Updated:** `competitor_data`
- **Output JSON:**
  ```json
  {
    "competitors": [
      {
        "name": "Competitor Name",
        "positioning": "Market positioning",
        "strengths": ["List of strengths"],
        "weaknesses": ["List of weaknesses"]
      }
    ],
    "competitive_landscape": "Summary of industry consolidation/crowdedness.",
    "company_positioning": "How the target company compares to competitors."
  }
  ```

#### **Market Agent** (`research_market`)
- **Role:** Expert industry analyst. Analyzes the broader market.
- **State Key Updated:** `market_data`
- **Output JSON:**
  ```json
  {
    "industry_overview": "Current state of the industry.",
    "market_size": "Estimated current TAM.",
    "growth_rate": "Estimated growth rate or CAGR.",
    "trends": ["List of current trends"],
    "risks": ["List of macro-level risks"],
    "opportunities": ["List of untapped opportunities"]
  }
  ```

#### **Financial Agent** (`research_financial`)
- **Role:** Corporate financial analyst. Estimates and summarizes financials.
- **State Key Updated:** `financial_data`
- **Output JSON:**
  ```json
  {
    "revenue": "Estimated annual revenue or scale.",
    "profitability": "Current profitability or margin profile.",
    "funding": "Known funding, public status, or capital structure.",
    "key_metrics": ["List of important financial KPIs"],
    "financial_risks": ["List of financial headwinds"]
  }
  ```

### 2. Evaluator Agents

#### **Data Validator** (`validate_data`)
- **Role:** Data QA Engineer. Reviews raw research from all researchers against a strict checklist (hard numbers, concrete TAM, specific competitors, concrete products).
- **State Keys Updated:** `missing_data_targets`, `research_feedback`, `data_iterations`
- **Output JSON:**
  ```json
  {
    "reasoning": "1-2 sentences explaining thought process.",
    "validation_status": "valid", // or "invalid"
    "feedback_summary": "Brief summary of approval/rejection.",
    "agent_feedback": {
      "research_financial": "Specific feedback for the financial agent to fix in the next iteration."
    }
  }
  ```

#### **Report Critic** (`critique_report`)
- **Role:** Executive Editor. Grades the final report draft purely on writing quality, synthesis, flow, and absence of redundancy.
- **State Keys Updated:** `report_score`, `report_feedback`
- **Output JSON:**
  ```json
  {
    "score": 8, // Integer 1-10
    "feedback": "Actionable instructions for the next draft."
  }
  ```

### 3. Synthesis Agent

#### **Writer** (`write_report`)
- **Role:** Senior Consultant. Synthesizes all gathered and validated data into a professional report.
- **State Keys Updated:** `report`, `report_iterations`
- **Output:** A formatted Markdown string containing the synthesized report.
