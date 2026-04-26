import os
from langchain_ollama import ChatOllama

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

llm = ChatOllama(
    model="llama3", 
    temperature=0, 
    base_url=OLLAMA_BASE_URL, 
    format="json"
)

writer_llm = ChatOllama(
    model="llama3", 
    temperature=0.4,
    base_url=OLLAMA_BASE_URL
)
