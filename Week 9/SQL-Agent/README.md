# View database

```
docker exec -it mock_postgres_db psql -U postgres -d northwind
```

# Build Porject
```
docker compose up -d --build
```

# Install ollama model
```
docker exec -it ollama_service ollama pull llama3
```
