from langchain.agents import create_agent
from langchain_ollama import ChatOllama
from src.tools import create_jira_ticket, move_jira_ticket, get_my_tasks
import os

ollama_url = os.environ.get("OLLAMA_BASE_URL", "http://ollama:11434")

llm = ChatOllama(
    model="llama3.1",
    base_url=ollama_url,
    temperature=0
)

tools = [create_jira_ticket, move_jira_ticket, get_my_tasks] # Added the new tool here

system_prompt = """You are a Jira Operations Expert working in Slack.
Your PRIMARY GOAL is to use your tools to assist the user with Jira tasks.

CRITICAL RULES:
1. The user CANNOT see the results of your tools. 
2. When you use the 'get_my_tasks' tool, YOU MUST explicitly read the tool's output and write out the exact tasks, ticket numbers, and due dates in your final message to the user.
3. NEVER assume the user saw the tool output. If the tool returns tasks, you must list them in your chat response.
4. If the user asks for "today" and "overdue" together, call the tool for each timeframe, and summarize both lists.
"""

graph = create_agent(llm, tools=tools, system_prompt=system_prompt)