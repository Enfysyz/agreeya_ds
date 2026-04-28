from langchain.agents import create_agent
from langchain_ollama import ChatOllama
from src.tools import create_jira_ticket, move_jira_ticket
import os

ollama_url = os.environ.get("OLLAMA_BASE_URL", "http://ollama:11434")

llm = ChatOllama(
    model="llama3.1",
    base_url=ollama_url,
    temperature=0
)

tools = [create_jira_ticket, move_jira_ticket]

# 1. Define the rules of engagement
system_prompt = """You are a helpful Jira integration assistant working in Slack. 
If the user greets you, asks a general question, or makes small talk, respond conversationally. 
ONLY use your tools if the user explicitly asks you to create, move, or modify a ticket. 
Never guess or invent ticket descriptions or project keys; ask the user for them if they are missing."""

# 2. Use the new v1.0 create_agent and the system_prompt argument
graph = create_agent(llm, tools=tools, system_prompt=system_prompt)