FROM python:3.11-slim

WORKDIR /app

# Install required system dependencies
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Install uv for fast dependency management and langgraph-cli
RUN pip install uv langgraph-cli[inmem]

# Copy application files
COPY . /app

# Install project dependencies
# (Ensure you have a pyproject.toml or requirements.txt containing:
# langgraph, langchain-ollama, jira, slack_bolt, etc.)
RUN uv pip install --system -e .

# Expose the port the LangGraph server will run on
EXPOSE 8000

# Start the LangGraph API server
CMD ["langgraph", "dev", "--host", "0.0.0.0", "--port", "8000"]