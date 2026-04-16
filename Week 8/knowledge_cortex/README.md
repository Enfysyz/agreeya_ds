# Folder Structure
```
KNOWLEDGE_CORTEX/
├── backend/
│   ├── docs/                   # 📄 DROP YOUR PDFS HERE
│   ├── src/
│   │   ├── main.py             # FastAPI entry point
│   │   ├── rag_engine.py       # LangChain setup, Hybrid Search, & Re-ranking
│   │   └── watcher.py          # Background service for auto-indexing
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── app.py                  # Streamlit UI
│   ├── Dockerfile
│   └── requirements.txt
├── docker-compose.yml          # Orchestrates Backend, Frontend, and Ollama
└── README.md
```

# Prerequisites
- Docker & Docker Compose
- NVIDIA Container Toolkit (optional)

# Start container
```
docker-compose up --build -d
```

# Download Ollama models
```
# Pull the generation model
docker exec -it ollama_service ollama pull llama3

# Pull the embedding model
docker exec -it ollama_service ollama pull nomic-embed-text
```

# API reference

## POST /query
Ask a question against your indexed documents.

**Request body** 
```
{
  "query": "Your question here?"
}
```

**Response Body**
```
{
  "answer": "The generated answer based on your documents.",
  "citations": [
    {
      "source": "backend/docs/filename.pdf",
      "content": "The specific text chunk used to generate the answer..."
    }
    "retrieval_transparency": [
        {
            "source": "file_path",
            "page": 1,
            "score": 0.0263,
            "content": "text from source document"
        }
  ]
}
```

## POST /files
List down the files in the backend/docs folder.

**Response Body**
```
{
  "total_files": 2,
  "indexed_files": [
    "backend/docs/file1.pdf",
    "backend/docs/file2.pdf"
  ]
}
```
