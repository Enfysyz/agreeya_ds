## Agent Logic (LangGraph)

The agent follows a cyclic graph pattern to ensure high-quality SQL generation and error recovery.

* **Node 1: `generate_sql`**: Analyzes the database schema and user intent to write a PostgreSQL query. It enforces strict rules regarding double-quoting and avoids hardcoding IDs.
* **Node 2: `execute_sql`**: Runs the query against the database. It includes a security guardrail to block destructive commands (DROP, DELETE, etc.) and a regex engine to fix common syntax errors automatically.
* **Node 3: `route_after_execution`**: A conditional edge. If the SQL fails, it sends the error back to the generator to "self-correct." It includes a **Circuit Breaker** that stops the loop after 3 failed attempts.
* **Node 4: `generate_reply`**: Formulates a human-friendly answer based on the retrieved data.


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
Table: "categories" - "CategoryID" (smallint) [PK] - "Picture" (bytea) - "CategoryName" (character varying) - "Description" (text) Table: "customercustomerdemo" - "CustomerID" (character) [PK] - "CustomerTypeID" (character) [PK] Table: "customerdemographics" - "CustomerTypeID" (character) [PK] - "CustomerDesc" (text) Table: "customers" - "CustomerID" (character) [PK] - "CompanyName" (character varying) - "ContactName" (character varying) - "ContactTitle" (character varying) - "Address" (character varying) - "City" (character varying) - "Region" (character varying) - "PostalCode" (character varying) - "Country" (character varying) - "Phone" (character varying) - "Fax" (character varying) Table: "employees" - "BirthDate" (date) - "Photo" (bytea) - "HireDate" (date) - "ReportsTo" (smallint) - "EmployeeID" (smallint) [PK] - "Address" (character varying) - "City" (character varying) - "Region" (character varying) - "PostalCode" (character varying) - "Country" (character varying) - "HomePhone" (character varying) - "Extension" (character varying) - "Notes" (text) - "PhotoPath" (character varying) - "LastName" (character varying) - "FirstName" (character varying) - "Title" (character varying) - "TitleOfCourtesy" (character varying) Table: "employeeterritories" - "EmployeeID" (smallint) [PK] - "TerritoryID" (character varying) [PK] Table: "order_details" - "OrderID" (smallint) [PK] - "ProductID" (smallint) [PK] - "UnitPrice" (real) - "Quantity" (smallint) - "Discount" (real) Table: "orders" - "OrderID" (smallint) [PK] - "EmployeeID" (smallint) - "OrderDate" (date) - "RequiredDate" (date) - "ShippedDate" (date) - "ShipVia" (smallint) - "Freight" (real) - "ShipCountry" (character varying) - "CustomerID" (character) - "ShipName" (character varying) - "ShipAddress" (character varying) - "ShipCity" (character varying) - "ShipRegion" (character varying) - "ShipPostalCode" (character varying) Table: "products" - "Discontinued" (integer) - "ReorderLevel" (smallint) - "ProductID" (smallint) [PK] - "SupplierID" (smallint) - "CategoryID" (smallint) - "UnitPrice" (real) - "UnitsInStock" (smallint) - "UnitsOnOrder" (smallint) - "ProductName" (character varying) - "QuantityPerUnit" (character varying) Table: "region" - "RegionID" (smallint) [PK] - "RegionDescription" (character) Table: "shippers" - "ShipperID" (smallint) [PK] - "CompanyName" (character varying) - "Phone" (character varying) Table: "shippers_tmp" - "ShipperID" (smallint) [PK] - "CompanyName" (character varying) - "Phone" (character varying) Table: "suppliers" - "SupplierID" (smallint) [PK] - "CompanyName" (character varying) - "ContactName" (character varying) - "ContactTitle" (character varying) - "Address" (character varying) - "City" (character varying) - "Region" (character varying) - "PostalCode" (character varying) - "Country" (character varying) - "Phone" (character varying) - "Fax" (character varying) - "HomePage" (text) Table: "territories" - "RegionID" (smallint) - "TerritoryID" (character varying) [PK] - "TerritoryDescription" (character) Table: "usstates" - "StateID" (smallint) - "StateName" (character varying) - "StateAbbr" (character varying) - "StateRegion" (character varying)
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

---

## 🛡️ Security & Reliability Features

* **Read-Only Enforcement**: The system uses a manual keyword check (`DROP`, `INSERT`, etc.) to prevent database modification.
* **Schema Injection**: The agent dynamically fetches the schema at runtime, meaning it adapts automatically if you add new tables to the database.
* **Auto-Quoting**: A specialized regex in `database.py` automatically wraps table and column names in double quotes (e.g., `c.Country` → `c."Country"`) to comply with PostgreSQL's case-sensitivity rules.
* **Self-Healing**: If the LLM generates a syntax error, the `retry_count` logic allows the agent to read the error message and rewrite its query.