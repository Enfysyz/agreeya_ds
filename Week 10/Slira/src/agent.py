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
class RouterOutput(BaseModel):
    intent: Literal["draft_ticket", "execute_ticket_creation", "move_ticket", "get_tasks", "get_daily_summary", "get_team_activity", "reply"] = Field(description="The action to take based on the user's request")
    
    ticket_summary: Optional[str] = Field(default=None, description="REQUIRED if intent is 'draft_ticket'. The title of the ticket")
    ticket_description: Optional[str] = Field(default=None, description="REQUIRED if intent is 'draft_ticket'. The detailed explanation")
    ticket_project_key: Optional[str] = Field(default=None, description="REQUIRED if intent is 'draft_ticket'. Project prefix (e.g., KAN)")
    ticket_issue_type: str = Field(default="Task", description="The type of ticket")
    ticket_due_date: Optional[str] = Field(default=None, description="The deadline formatted exactly as YYYY-MM-DD")
    
    move_issue_key: Optional[str] = Field(default=None, description="The full ticket ID (e.g., KAN-123)")
    move_transition_name: Optional[str] = Field(default=None, description="REQUIRED if intent is 'move_ticket'. The name of the status to move it to (e.g., 'In Progress', 'Done')")
    
    tasks_timeframe: Literal["today", "overdue", "all"] = Field(default="all", description="Timeframe for the tasks")
    
    activity_project_key: Optional[str] = Field(default=None, description="Optional project key to filter by")
    
    reply_message: Optional[str] = Field(default=None, description="The message to send back to the user")

# --- STATE DEFINITION ---
class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    router_output: Optional[RouterOutput]
    draft_ticket_params: Optional[dict]
    last_issue_key: Optional[str]

system_prompt = """You are a Jira Operations Expert working in Slack.
Your PRIMARY GOAL is to assist the user with Jira tasks.

*** HUMAN-IN-THE-LOOP TICKET CREATION WORKFLOW ***
If the user asks you to create a ticket (or create one based on a thread), YOU MUST NEVER execute 'CREATE' action immediately. You must follow these exact steps:
- STEP 1 (Draft): Select 'draft_ticket' intent and YOU MUST provide ticket_summary, ticket_description, and ticket_project_key.
- STEP 2 (Present): The system will automatically present the draft.
- STEP 3 (Wait & Act): If the user replies with "yes" or confirms the draft, ONLY THEN select 'execute_ticket_creation' intent.
*** MOVING TICKETS ***
If the user asks to move a ticket to a new status (e.g., "move it to in progress"):
- Select 'move_ticket' intent.
- YOU MUST extract the status name into `move_transition_name` (e.g., "In Progress").
- DO NOT put the status name into `ticket_project_key` or any other field!
"""

def router_node(state: AgentState):
    messages = state["messages"]
    sys_msg = SystemMessage(content=system_prompt)
    prompt = [sys_msg] + messages
    structured_llm = llm.with_structured_output(RouterOutput)
    response = structured_llm.invoke(prompt)
    print(f"DEBUG [router_node] LLM Raw Response: {response}")
    return {"router_output": response}

def route_after_router(state: AgentState):
    router_out = state.get("router_output")
    if not router_out:
        return "reply_node"
    
    intent = getattr(router_out, "intent", "reply") if not isinstance(router_out, dict) else router_out.get("intent", "reply")
    if intent in ["draft_ticket", "execute_ticket_creation"]:
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
    
    if intent == "execute_ticket_creation":
        draft = state.get("draft_ticket_params")
        if not draft:
            return {"messages": [AIMessage(content="I don't have a drafted ticket to create. Please provide the details again.")]}
        
        draft["action"] = "CREATE"
        result = create_jira_ticket(**draft)
        
        # Extract the new issue key to save in state memory
        import re
        match = re.search(r'ticket:\s*([A-Z]+-\d+)', result)
        last_key = match.group(1) if match else None
        
        return {
            "messages": [AIMessage(content=result)], 
            "draft_ticket_params": None,
            "last_issue_key": last_key
        }
    
    if isinstance(router_out, dict):
        summary = router_out.get("ticket_summary")
        description = router_out.get("ticket_description")
        project_key = router_out.get("ticket_project_key")
        issue_type = router_out.get("ticket_issue_type", "Task")
        due_date = router_out.get("ticket_due_date")
    else:
        summary = getattr(router_out, "ticket_summary", None)
        description = getattr(router_out, "ticket_description", None)
        project_key = getattr(router_out, "ticket_project_key", None)
        issue_type = getattr(router_out, "ticket_issue_type", "Task")
        due_date = getattr(router_out, "ticket_due_date", None)

    if not summary or not project_key:
        return {"messages": [AIMessage(content="I'm missing the required parameters to create a ticket. (Debug: the model failed to output flat ticket_summary or ticket_project_key).")]}
        
    result = create_jira_ticket(
        summary=summary,
        description=description,
        project_key=project_key,
        action="DRAFT",
        issue_type=issue_type,
        due_date=due_date
    )
    
    return {
        "messages": [AIMessage(content=result)],
        "draft_ticket_params": {
            "summary": summary,
            "description": description,
            "project_key": project_key,
            "action": "DRAFT",
            "issue_type": issue_type,
            "due_date": due_date
        }
    }

def move_ticket_node(state: AgentState):
    router_out = state.get("router_output")
    if isinstance(router_out, dict):
        issue_key = router_out.get("move_issue_key")
        transition_name = router_out.get("move_transition_name")
    else:
        issue_key = getattr(router_out, "move_issue_key", None)
        transition_name = getattr(router_out, "move_transition_name", None)

    if not issue_key and state.get("last_issue_key"):
        issue_key = state.get("last_issue_key")

    if not issue_key or not transition_name:
        return {"messages": [AIMessage(content="I'm missing the required parameters to move a ticket.")]}
        
    result = move_jira_ticket(issue_key=issue_key, transition_name=transition_name)
    return {
        "messages": [AIMessage(content=result)],
        "last_issue_key": issue_key
    }

def get_tasks_node(state: AgentState):
    router_out = state.get("router_output")
    if isinstance(router_out, dict):
        timeframe = router_out.get("tasks_timeframe", "all")
    else:
        timeframe = getattr(router_out, "tasks_timeframe", "all")
        
    result = get_my_tasks(timeframe=timeframe)
    return {"messages": [AIMessage(content=result)]}

def get_daily_summary_node(state: AgentState):
    result = get_daily_summary()
    return {"messages": [AIMessage(content=result)]}

def get_team_activity_node(state: AgentState):
    router_out = state.get("router_output")
    if isinstance(router_out, dict):
        project_key = router_out.get("activity_project_key")
    else:
        project_key = getattr(router_out, "activity_project_key", None)
        
    result = get_team_activity(project_key=project_key)
    return {"messages": [AIMessage(content=result)]}

def reply_node(state: AgentState):
    router_out = state.get("router_output")
    if isinstance(router_out, dict):
        message = router_out.get("reply_message", "I processed your request, but have no explicit text response.")
    else:
        message = getattr(router_out, "reply_message", "I processed your request, but have no explicit text response.")
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