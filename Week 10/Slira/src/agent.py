from typing import TypedDict, Annotated, Literal, Optional
from pydantic import BaseModel, Field
import os

from langchain_core.messages import BaseMessage, SystemMessage, AIMessage
from langgraph.graph import StateGraph, START, END, add_messages
from langchain_ollama import ChatOllama

from src.tools import (
    create_jira_ticket, move_jira_ticket, get_my_tasks, 
    get_daily_summary, get_team_activity
)

ollama_url = os.environ.get("OLLAMA_BASE_URL", "http://ollama:11434")

llm = ChatOllama(
    model="llama3.1",
    base_url=ollama_url,
    temperature=0
)

# --- STRUCTURED OUTPUT MODELS ---
class CreateTicketParams(BaseModel):
    summary: str = Field(description="The title or short name of the ticket")
    description: str = Field(description="The detailed explanation of the ticket")
    project_key: str = Field(description="The short, uppercase prefix of the project (e.g., KAN, DEV, PROJ)")
    action: Literal["DRAFT", "CREATE"] = Field(default="DRAFT", description="Use DRAFT first, only use CREATE if explicitly approved")
    issue_type: str = Field(default="Task", description="The type of ticket")
    due_date: Optional[str] = Field(default=None, description="The deadline formatted exactly as YYYY-MM-DD")

class MoveTicketParams(BaseModel):
    issue_key: str = Field(description="The full ticket ID (e.g., KAN-123)")
    transition_name: str = Field(description="The name of the status to move it to")

class GetTasksParams(BaseModel):
    timeframe: Literal["today", "overdue", "all"] = Field(default="all", description="Timeframe for the tasks")

class GetTeamActivityParams(BaseModel):
    project_key: Optional[str] = Field(default=None, description="Optional project key to filter by")

class ReplyParams(BaseModel):
    message: str = Field(description="The message to send back to the user")

class RouterOutput(BaseModel):
    intent: Literal["create_ticket", "confirm_ticket_creation", "move_ticket", "get_tasks", "get_daily_summary", "get_team_activity", "reply"] = Field(description="The action to take based on the user's request")
    create_ticket_params: Optional[CreateTicketParams] = Field(default=None, description="REQUIRED if intent is 'create_ticket'")
    move_ticket_params: Optional[MoveTicketParams] = Field(default=None, description="REQUIRED if intent is 'move_ticket'")
    get_tasks_params: Optional[GetTasksParams] = Field(default=None, description="REQUIRED if intent is 'get_tasks'")
    get_team_activity_params: Optional[GetTeamActivityParams] = Field(default=None, description="REQUIRED if intent is 'get_team_activity'")
    reply_params: Optional[ReplyParams] = Field(default=None, description="REQUIRED if intent is 'reply'")

# --- STATE DEFINITION ---
class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    router_output: Optional[RouterOutput]
    draft_ticket_params: Optional[dict]

system_prompt = """You are a Jira Operations Expert working in Slack.
Your PRIMARY GOAL is to assist the user with Jira tasks.

*** HUMAN-IN-THE-LOOP TICKET CREATION WORKFLOW ***
If the user asks you to create a ticket (or create one based on a thread), YOU MUST NEVER execute 'CREATE' action immediately. You must follow these exact steps:
- STEP 1 (Draft): Select 'create_ticket' intent and YOU MUST fully populate the `create_ticket_params` object (including summary, description, and project_key). Set action='DRAFT'. Do NOT put the draft in reply_params.
- STEP 2 (Present): The system will automatically present the draft.
- STEP 3 (Wait & Act): If the user replies with "yes" or confirms the draft, ONLY THEN select 'confirm_ticket_creation' intent. You do NOT need to populate any params for confirm_ticket_creation!
"""

def router_node(state: AgentState):
    messages = state["messages"]
    sys_msg = SystemMessage(content=system_prompt)
    prompt = [sys_msg] + messages
    structured_llm = llm.with_structured_output(RouterOutput)
    response = structured_llm.invoke(prompt)
    return {"router_output": response}

def route_after_router(state: AgentState):
    router_out = state.get("router_output")
    if not router_out:
        return "reply_node"
    
    intent = getattr(router_out, "intent", "reply") if not isinstance(router_out, dict) else router_out.get("intent", "reply")
    if intent in ["create_ticket", "confirm_ticket_creation"]:
        return "create_ticket_node"
    elif intent == "move_ticket":
        return "move_ticket_node"
    elif intent == "get_tasks":
        return "get_tasks_node"
    elif intent == "get_daily_summary":
        return "get_daily_summary_node"
    elif intent == "get_team_activity":
        return "get_team_activity_node"
    else:
        return "reply_node"

def create_ticket_node(state: AgentState):
    router_out = state.get("router_output")
    intent = getattr(router_out, "intent", "reply") if router_out and not isinstance(router_out, dict) else (router_out.get("intent", "reply") if router_out else "reply")
    
    if intent == "confirm_ticket_creation":
        draft = state.get("draft_ticket_params")
        if not draft:
            return {"messages": [AIMessage(content="I don't have a drafted ticket to create. Please provide the details again.")]}
        
        draft["action"] = "CREATE"
        result = create_jira_ticket(**draft)
        return {"messages": [AIMessage(content=result)], "draft_ticket_params": None}
    
    params = state.get("router_output").create_ticket_params if state.get("router_output") else None
    if not params:
        return {"messages": [AIMessage(content="I'm missing the required parameters to create a ticket.")]}
        
    result = create_jira_ticket(
        summary=params.summary,
        description=params.description,
        project_key=params.project_key,
        action=params.action,
        issue_type=params.issue_type,
        due_date=params.due_date
    )
    
    if params.action.upper() == "DRAFT":
        return {
            "messages": [AIMessage(content=result)],
            "draft_ticket_params": {
                "summary": params.summary,
                "description": params.description,
                "project_key": params.project_key,
                "action": "DRAFT",
                "issue_type": params.issue_type,
                "due_date": params.due_date
            }
        }
    else:
        return {"messages": [AIMessage(content=result)], "draft_ticket_params": None}

def move_ticket_node(state: AgentState):
    params = state.get("router_output").move_ticket_params if state.get("router_output") else None
    if not params:
        return {"messages": [AIMessage(content="I'm missing the required parameters to move a ticket.")]}
        
    result = move_jira_ticket(issue_key=params.issue_key, transition_name=params.transition_name)
    return {"messages": [AIMessage(content=result)]}

def get_tasks_node(state: AgentState):
    params = state.get("router_output").get_tasks_params if state.get("router_output") else None
    timeframe = params.timeframe if params and hasattr(params, 'timeframe') else "all"
        
    result = get_my_tasks(timeframe=timeframe)
    return {"messages": [AIMessage(content=result)]}

def get_daily_summary_node(state: AgentState):
    result = get_daily_summary()
    return {"messages": [AIMessage(content=result)]}

def get_team_activity_node(state: AgentState):
    params = state.get("router_output").get_team_activity_params if state.get("router_output") else None
    project_key = params.project_key if params else None
    result = get_team_activity(project_key=project_key)
    return {"messages": [AIMessage(content=result)]}

def reply_node(state: AgentState):
    router_out = state.get("router_output")
    if router_out and hasattr(router_out, "reply_params") and router_out.reply_params:
        message = router_out.reply_params.message
    else:
        message = "I processed your request, but have no explicit text response."
    return {"messages": [AIMessage(content=message)]}

builder = StateGraph(AgentState)

builder.add_node("router", router_node)
builder.add_node("create_ticket_node", create_ticket_node)
builder.add_node("move_ticket_node", move_ticket_node)
builder.add_node("get_tasks_node", get_tasks_node)
builder.add_node("get_daily_summary_node", get_daily_summary_node)
builder.add_node("get_team_activity_node", get_team_activity_node)
builder.add_node("reply_node", reply_node)

builder.add_edge(START, "router")
builder.add_conditional_edges("router", route_after_router)
builder.add_edge("create_ticket_node", END)
builder.add_edge("move_ticket_node", END)
builder.add_edge("get_tasks_node", END)
builder.add_edge("get_daily_summary_node", END)
builder.add_edge("get_team_activity_node", END)
builder.add_edge("reply_node", END)

graph = builder.compile()