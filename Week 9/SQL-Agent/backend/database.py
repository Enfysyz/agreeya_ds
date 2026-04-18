from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

# Connect to the PostgreSQL container over the Docker network
# 'postgres' is the user, 'secretpassword' is the password, 'db' is the container name
DATABASE_URL = "postgresql://postgres:secretpassword@db:5432/northwind"

engine = create_engine(DATABASE_URL)

def get_database_schema() -> str:
    """Fetches all table names and their column definitions."""
    schema_info = ""
    try:
        with engine.connect() as conn:
            # Query to get all tables in the public schema
            tables_query = text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
            """)
            tables = conn.execute(tables_query).fetchall()
            
            for table in tables:
                table_name = table[0]
                schema_info += f"Table: {table_name}\n"
                
                # Query to get columns for each table
                columns_query = text(f"""
                    SELECT column_name, data_type 
                    FROM information_schema.columns 
                    WHERE table_name = '{table_name}'
                """)
                columns = conn.execute(columns_query).fetchall()
                for col in columns:
                    schema_info += f"  - {col[0]} ({col[1]})\n"
                schema_info += "\n"
        return schema_info
    except Exception as e:
        return f"Error fetching schema: {str(e)}"

def execute_read_only_query(sql_query: str) -> dict:
    """Safely executes a query, blocking modifications."""
    
    # Very basic Guardrail: Block destructive commands
    forbidden_keywords = ["DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "TRUNCATE"]
    upper_query = sql_query.upper()
    if any(keyword in upper_query for keyword in forbidden_keywords):
        return {"error": "Security Violation: Only SELECT queries are allowed."}

    try:
        with engine.connect() as conn:
            result = conn.execute(text(sql_query))
            # Fetch column names
            keys = result.keys()
            # Fetch data rows and convert to list of dicts
            data = [dict(zip(keys, row)) for row in result.fetchall()]
            return {"data": data}
    except SQLAlchemyError as e:
        # Return the exact DB error so LangGraph can pass it back to the LLM to fix
        return {"error": str(e)}