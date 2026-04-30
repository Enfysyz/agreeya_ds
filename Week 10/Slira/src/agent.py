from langchain.agents import create_agent
from langchain_ollama import ChatOllama
# 1. Import the new team tool
from src.tools import create_jira_ticket, move_jira_ticket, get_my_tasks, get_daily_summary, get_team_activity
import os

ollama_url = os.environ.get("OLLAMA_BASE_URL", "http://ollama:11434")

llm = ChatOllama(
    model="llama3.1",
    base_url=ollama_url,
    temperature=0
)

# 2. Add the new tool to the list
tools = [create_jira_ticket, move_jira_ticket, get_my_tasks, get_daily_summary, get_team_activity]

# 3. Update the instructions to distinguish between "my" and "team" queries
system_prompt = """You are a Jira Operations Expert working in Slack.
Your PRIMARY GOAL is to use your tools to assist the user with Jira tasks.

CRITICAL RULES:
1. The user CANNOT see the results of your tools. YOU MUST explicitly read the tool's output and format it for the user.
2. NEVER assume the user saw the tool output.

*** HUMAN-IN-THE-LOOP TICKET CREATION WORKFLOW ***
If the user asks you to create a ticket (or create one based on a thread), YOU MUST NEVER call the 'create_jira_ticket' tool immediately. You must follow these exact steps:
- STEP 1 (Draft): Read the conversation and generate a draft.
- STEP 2 (Present): Send a message to the user formatted exactly like this:
  "Here is the draft for your ticket:
  *Project:* [Key]
  *Summary:* [Title]
  *Description:* [Description]
  *Due Date:* [Date (YYYY-MM-DD) or N/A]
  
  Should I go ahead and create this ticket?"
- STEP 3 (Wait & Act): Stop and wait for the user to reply. 
  - If they reply with "yes" or confirm, ONLY THEN call the `create_jira_ticket` tool.
  - If they ask for changes, provide a new draft and ask for confirmation again.
"""

graph = create_agent(llm, tools=tools, system_prompt=system_prompt)