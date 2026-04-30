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
1. The user CANNOT see the results of your tools. 
2. When you use tools, YOU MUST explicitly read the tool's output and write out the exact tasks, ticket numbers, assignees, and statuses in your final message.
3. NEVER assume the user saw the tool output.
4. If the user asks for "my summary" or "my status", use the 'get_daily_summary' tool.
5. If the user asks about the "team", "everyone", or "project activity", use the 'get_team_activity' tool. If they mention a specific project (like KAN), pass it as the project_key.
"""

graph = create_agent(llm, tools=tools, system_prompt=system_prompt)