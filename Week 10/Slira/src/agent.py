from langchain.agents import create_agent
from langchain_ollama import ChatOllama
from src.tools import create_jira_ticket, move_jira_ticket
import os

# Notice the base_url points to the docker service name "ollama"
ollama_url = os.environ.get("OLLAMA_BASE_URL", "http://ollama:11434")

# Initialize the LLM
llm = ChatOllama(
    model="llama3.1", # Or your preferred tool-calling model
    base_url=ollama_url,
    temperature=0
)

# Bind tools
tools = [create_jira_ticket, move_jira_ticket]

# Create the LangGraph agent
graph = create_agent(llm, tools=tools)