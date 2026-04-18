import json
from typing import TypedDict, Annotated, Sequence
from langgraph.graph import StateGraph, END
from langchain_community.chat_models import ChatOllama
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
import database

class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], "The chat history"]
    sql_query: str
    agent_reply: str  # <--- New field to hold the LLM's conversation
    error: str
    data: dict

# Initialize Ollama and FORCE it to only output valid JSON
llm = ChatOllama(
    model="llama3", 
    temperature=0, 
    base_url="http://ollama:11434",
    format="json"  # <--- This is the magic bullet
)

def generate_sql(state: AgentState):
    schema = database.get_database_schema()
    messages = state.get("messages", [])
    error = state.get("error", "")
    
    # Updated Prompt to enforce JSON
    system_prompt = f"""You are an expert PostgreSQL data analyst.
        You MUST respond in valid JSON format with exactly two keys: "sql" and "reply".
        - "sql": The raw PostgreSQL query to execute. If no database query is needed to answer the user, leave this as an empty string "".
        - "reply": Your conversational answer, explanation, or direct response to the user.

        Here is the database schema:
        {schema}
        """
    
    if error:
        system_prompt += f"\nURGENT: Your last SQL query failed with this error: {error}\nRewrite the SQL to fix it."

    full_messages = [SystemMessage(content=system_prompt)] + list(messages)
    response = llm.invoke(full_messages)
    
    try:
        # Parse the JSON response from the LLM
        parsed = json.loads(response.content)
        sql_query = parsed.get("sql", "").strip()
        agent_reply = parsed.get("reply", "").strip()
        
        return {"sql_query": sql_query, "agent_reply": agent_reply, "error": ""}
    except Exception as e:
        print(f"JSON Parsing Error: {response.content}")
        return {"error": "Failed to parse JSON from LLM.", "sql_query": ""}

def execute_sql(state: AgentState):
    query = state.get("sql_query")
    
    # NEW LOGIC: If the LLM decided no SQL was needed, skip execution entirely!
    if not query:
        print("\n[Agent]: No SQL needed. Skipping execution.\n")
        return {"data": {}, "error": ""}
        
    print(f"\n[Agent Executing]: {query}\n")
    
    result = database.execute_read_only_query(query)
    
    if "error" in result:
        return {"error": result["error"], "data": {}}
    else:
        return {"data": result["data"], "error": ""}

def route_after_execution(state: AgentState):
    if state.get("error"):
        print(f"[Agent Error Caught]: {state.get('error')} -> Rewriting...")
        return "generate_sql"
    return END

# Build Graph
workflow = StateGraph(AgentState)
workflow.add_node("generate_sql", generate_sql)
workflow.add_node("execute_sql", execute_sql)
workflow.set_entry_point("generate_sql")
workflow.add_edge("generate_sql", "execute_sql")
workflow.add_conditional_edges("execute_sql", route_after_execution)

agent_app = workflow.compile()