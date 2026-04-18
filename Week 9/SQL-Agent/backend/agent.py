from typing import TypedDict, Annotated, Sequence
from langgraph.graph import StateGraph, END
from langchain_community.chat_models import ChatOllama
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
import database

# 1. Define the State
# This holds the memory for a single run through the graph
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], "The chat history"]
    sql_query: str
    error: str
    data: dict

# 2. Initialize the Local LLM
# Make sure Ollama is running 'llama3' on your host machine
llm = ChatOllama(
    model="llama3", 
    temperature=0, 
    base_url="http://ollama:11434" # Connects to local host from inside Docker
)

# 3. Node: Generate SQL
def generate_sql(state: AgentState):
    schema = database.get_database_schema()
    messages = state.get("messages", [])
    error = state.get("error", "")
    
    # System prompt forces the AI to act strictly as a SQL generator
    system_prompt = f"""You are an expert PostgreSQL data analyst.
Your job is to write a SQL query that answers the user's request.
ONLY output the raw SQL query. Do not wrap it in markdown code blocks (no ```sql).
Do not include any explanations.

Here is the database schema:
{schema}
"""
    
    # If the previous run had an error, tell the AI to fix it
    if error:
        system_prompt += f"\nURGENT: Your last query failed with this error: {error}\nRewrite the SQL to fix it."

    full_messages = [SystemMessage(content=system_prompt)] + list(messages)
    
    response = llm.invoke(full_messages)
    # Clean up any accidental markdown the LLM might have added
    clean_sql = response.content.replace("```sql", "").replace("```", "").strip()
    
    return {"sql_query": clean_sql, "error": ""} # Clear previous errors

# 4. Node: Execute SQL
def execute_sql(state: AgentState):
    query = state.get("sql_query")
    print(f"\n[Agent Executing]: {query}\n") # Helpful for your terminal logs
    
    result = database.execute_read_only_query(query)
    
    if "error" in result:
        return {"error": result["error"], "data": {}}
    else:
        return {"data": result["data"], "error": ""}

# 5. Routing Logic (The ReAct Loop)
def route_after_execution(state: AgentState):
    # If there's an error, loop back and try again
    if state.get("error"):
        print(f"[Agent Error Caught]: {state.get('error')} -> Rewriting...")
        return "generate_sql"
    # Otherwise, finish the graph
    return END

# 6. Build the Graph
workflow = StateGraph(AgentState)

workflow.add_node("generate_sql", generate_sql)
workflow.add_node("execute_sql", execute_sql)

workflow.set_entry_point("generate_sql")
workflow.add_edge("generate_sql", "execute_sql")
workflow.add_conditional_edges("execute_sql", route_after_execution)

# Compile the final application
agent_app = workflow.compile()