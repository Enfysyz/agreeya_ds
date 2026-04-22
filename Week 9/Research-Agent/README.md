# Deep Research AI Agent

An automated, containerized AI research agent that searches the web and synthesizes findings into a comprehensive report entirely locally using Ollama. 

## Prerequisites
- **Docker** and **Docker Compose** installed.
- (Optional but recommended) **NVIDIA Container Toolkit** if you intend to run Ollama with GPU acceleration.


## Installation & Setup
### Build container
```
docker-compose up --build -d
```

### Install LLM Model
```
docker exec -it ollama_research ollama pull llama3  
```

## API Documentation
### POST /api/research
The endpoint responds with a text/event-stream (Server-Sent Events), yielding real-time JSON logs followed by the final synthesized report.
```
data: {"type": "log", "message": "Initializing Deep Research protocol..."}

data: {"type": "log", "message": "Found source: Article Title", "url": "[https://example.com](https://example.com)"}

data: {"type": "log", "message": "Navigating and extracting content...", "url": "[https://example.com](https://example.com)"}

data: {"type": "log", "message": "Navigating and extracting content...", "url": "[https://example.com](https://example.com)"}

data: {"type": "complete", "result": "The final synthesized comprehensive report..."}
```