import json
from typing import TypedDict, Annotated, Sequence
from langgraph.graph import StateGraph, END
from langchain_community.chat_models import ChatOllama
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
import database

# 1. ADD RETRY_COUNT TO STATE
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], "The chat history"]
    sql_query: str
    agent_reply: str  
    error: str
    data: dict
    retry_count: int  # <--- New field

llm_json_mode = ChatOllama(model="llama3", temperature=0, base_url="http://ollama:11434", format="json")
llm_chat_mode = ChatOllama(model="llama3", temperature=0.3, base_url="http://ollama:11434")

def generate_sql(state: AgentState):
    schema = database.get_database_schema()
    messages = state.get("messages", [])
    error = state.get("error", "")
    
    system_prompt = f"""You are an expert PostgreSQL data analyst.
        You MUST respond in valid JSON format with exactly one key: "sql".
        - "sql": The raw PostgreSQL query to execute. 

        CRITICAL POSTGRESQL RULE:
        You MUST copy the exact double-quoted table and column names from the schema below.
        If you use table aliases, the quotes ONLY go around the column name, not the alias.

        META-QUESTIONS RULE:
        If the user asks about the database structure itself (e.g., "What tables exist?", "Name the tables", "What columns are in customers?"), DO NOT write a SQL query. You already have the schema below. Return an empty string "" for the sql key.

        NO MAGIC IDS RULE:
        Do NOT guess or hardcode integer IDs (like ShipperID, CategoryID, etc.) based on text names in the prompt. You must ALWAYS use a JOIN or a subquery to filter by text names dynamically.
        Correct: ... JOIN "shippers" s ON o."ShipVia" = s."ShipperID" WHERE s."CompanyName" ILIKE '%UPS%'
        Wrong: ... WHERE o."ShipVia" = 3

        EXAMPLE OUTPUT FOR DATA QUERY:
        {{"sql": "SELECT c.\\"Country\\", c.\\"CompanyName\\" FROM \\"customers\\" c ORDER BY c.\\"Country\\""}}

        EXAMPLE OUTPUT FOR META-QUESTION:
        {{"sql": ""}}

        Here is the database schema:
        {schema}
        """
    if error:
        system_prompt += f"\nURGENT: Your last SQL query failed with this error: {error}\nRewrite the SQL to fix it. Make sure you are using double quotes around ALL column names."

    full_messages = [SystemMessage(content=system_prompt)] + list(messages)
    response = llm_json_mode.invoke(full_messages)
    
    # 2. RAW LOGGING: Print exactly what the LLM generated
    print(f"\n========== RAW LLM OUTPUT ==========\n{response.content}\n====================================\n")
    
    try:
        parsed = json.loads(response.content)
        sql_query = parsed.get("sql", "").strip()
        return {"sql_query": sql_query, "error": ""}
    except Exception as e:
        return {"error": "Failed to parse JSON from LLM.", "sql_query": ""}

def execute_sql(state: AgentState):
    current_retries = state.get("retry_count", 0)
    
    # 1. PRESERVE PREVIOUS ERRORS (like JSON parse failures)
    if state.get("error"):
        return {"error": state.get("error"), "data": {}, "retry_count": current_retries + 1}

    query = state.get("sql_query")
    
    # 2. Skip execution if query is empty (but only if there wasn't an error)
    if not query:
        return {"data": {}, "error": "", "retry_count": current_retries}
        
    print(f"\n[Agent Executing]: {query}\n")
    result = database.execute_read_only_query(query)
    
    if "error" in result:
        return {"error": result["error"], "data": {}, "retry_count": current_retries + 1}
    else:
        return {"data": result["data"], "error": "", "retry_count": 0}

# --- NODE 3: Formulate Final Reply ---
def generate_reply(state: AgentState):
    if state.get("error") and state.get("retry_count", 0) >= 3:
        return {"agent_reply": f"I'm sorry, I failed to generate a valid SQL query after 3 attempts. The database returned this error: {state.get('error')}"}

    messages = state.get("messages", [])
    user_query = messages[-1].content if messages else ""
    sql_query = state.get("sql_query", "")
    db_data = state.get("data", [])

    # 1. THE ENGINEERING FIX: Truncate data to save LLM tokens
    total_rows = len(db_data) if isinstance(db_data, list) else 0
    preview_data = db_data[:5] if isinstance(db_data, list) else db_data

    # 2. THE PROMPT FIX: Instruct the LLM to act like a dashboard assistant
    system_prompt = f"""You are the final response agent for a data analytics platform.
        User asked: {user_query}
        SQL Executed: {sql_query}
        Total Rows Found: {total_rows}
        Data Preview (First 5 rows): {json.dumps(preview_data, default=str)}

        Write the final response directly to the user. Do not include markdown code blocks. 

        CRITICAL RULES:
        1. If 'Total Rows Found' is 0, explicitly state that no data was found. DO NOT hallucinate.
        2. DO NOT regurgitate or list the data rows in your text reply. The frontend UI will display the raw data in a visual table automatically.
        3. Keep your reply incredibly brief and conversational. Just confirm what you found. (e.g., "I found {total_rows} customers matching your request. Here is the data:").
        4. NO DATA ANALYSIS: You only have a 5-row preview. NEVER attempt to summarize trends, state maximums/minimums, or make comparative claims (e.g., "X is higher than Y"). You do not have the full picture. Stick to simply introducing the data.
        """

    response = llm_chat_mode.invoke([SystemMessage(content=system_prompt)])
    return {"agent_reply": response.content}

def route_after_execution(state: AgentState):
    if state.get("error"):
        # 5. THE CIRCUIT BREAKER
        if state.get("retry_count", 0) >= 3:
            print(f"\n[Circuit Breaker]: Max retries (3) reached. Aborting loop.\n")
            return "generate_reply"
            
        print(f"[Agent Error Caught]: {state.get('error')} -> Rewriting (Attempt {state.get('retry_count')}/3)...")
        return "generate_sql"
        
    return "generate_reply"

workflow = StateGraph(AgentState)
workflow.add_node("generate_sql", generate_sql)
workflow.add_node("execute_sql", execute_sql)
workflow.add_node("generate_reply", generate_reply)

workflow.set_entry_point("generate_sql")
workflow.add_edge("generate_sql", "execute_sql")
workflow.add_conditional_edges("execute_sql", route_after_execution)
workflow.add_edge("generate_reply", END)

agent_app = workflow.compile()