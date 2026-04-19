# QueryPilot: Analyst-in-the-Loop
QueryPilot is a smart, local-first analytics assistant that lets anyone chat with their database using plain English instead of complex SQL code. Under the hood, a Python-based AI agent (powered by LangGraph and Llama 3) translates your questions into safe database queries, automatically double-checks its own work to fix any errors, and fetches the requested information from a PostgreSQL database. It then sends back a friendly, conversational summary alongside the raw data, which a custom React frontend instantly renders into clean, interactive tables—making data exploration seamless, secure, and accessible for non-technical users.

<video width="1300"  controls>
  <source src="media\qp_demo.mp4" type="video/mp4">
</video>

## Agent Logic 

The agent follows a cyclic graph pattern to ensure high-quality SQL generation and error recovery.

* **Node 1: `generate_sql`**: Analyzes the database schema and user intent to write a PostgreSQL query. It enforces strict rules regarding double-quoting and avoids hardcoding IDs.
* **Node 2: `execute_sql`**: Runs the query against the database. It includes a security guardrail to block destructive commands (DROP, DELETE, etc.) and a regex engine to fix common syntax errors automatically.
* **Node 3: `route_after_execution`**: A conditional edge. If the SQL fails, it sends the error back to the generator to "self-correct." It includes a **Circuit Breaker** that stops the loop after 3 failed attempts.
* **Node 4: `generate_reply`**: Formulates a human-friendly answer based on the retrieved data.

<!-- ![Agent Workflow](img\SQL-Agent.png) -->
<img src="media\SQL-Agent.png" width="1300">


## Setup & Installation

### 1. Prerequisites
* Docker and Docker Compose installed.
* NVIDIA GPU (Optional, for Ollama acceleration).

### 2. Launch Services
Build and start the containers:
```bash
docker compose up -d --build
```

### 3. Initialize the Model
Download the Llama3 model into the Ollama container:
```bash
docker exec -it ollama_service ollama pull llama3
```

# View database

```
docker exec -it mock_postgres_db psql -U postgres -d northwind
```

## 🔌 API Documentation

### **GET** `/api/schema`
Fetches the current database schema as perceived by the agent. Useful for debugging if the agent claims it "cannot see" a table.
```
Table: users

id (int) [PK]
name (varchar)
email (varchar)
created_at (date)

Table: orders

id (int) [PK]
user_id (int) [FK → users]
total_amount (decimal)
created_at (date)

Table: order_items

order_id (int) [PK, FK → orders]
product_id (int) [PK, FK → products]
quantity (int)

Table: products

id (int) [PK]
name (varchar)
price (decimal)
stock (int)
```

### **POST** `/api/chat`
The main entry point for queries.
* **Payload**: `{"message": "Who are our top 5 customers in France?"}`
* **Response**:
    ```json
    {
      "reply": "The top 5 customers in France are...",
      "sql_generated": "SELECT ...",
      "data_result": [...]
    }
    ```

## Frontend Architecture
```
frontend/
├── src/
│   ├── api.ts                    # API client (GET /api/schema, POST /api/chat)
│   ├── types.ts                  # TypeScript interfaces
│   ├── App.tsx                   # Main layout: sidebar + chat + input
│   ├── index.css                 # ShadCN light theme with custom styling
│   ├── utils/
│   │   └── parseSchema.ts        # Schema string → structured table/column objects
│   └── components/
│       ├── SchemaPanel.tsx        # Collapsible database schema sidebar
│       ├── ChatMessage.tsx        # User/assistant message bubbles
│       ├── ChatInput.tsx          # Input bar with suggestion chips
│       ├── SqlCodeBlock.tsx       # Syntax-highlighted SQL with copy button
│       └── DataTable.tsx          # Paginated results table with CSV export
```
## Security & Reliability Features

* **Read-Only Enforcement**: The system uses a manual keyword check (`DROP`, `INSERT`, etc.) to prevent database modification.
* **Schema Injection**: The agent dynamically fetches the schema at runtime, meaning it adapts automatically if you add new tables to the database.
* **Auto-Quoting**: A specialized regex in `database.py` automatically wraps table and column names in double quotes (e.g., `c.Country` → `c."Country"`) to comply with PostgreSQL's case-sensitivity rules.
* **Self-Healing**: If the LLM generates a syntax error, the `retry_count` logic allows the agent to read the error message and rewrite its query.