import re
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

# Connect to the PostgreSQL container over the Docker network
# 'postgres' is the user, 'secretpassword' is the password, 'db' is the container name
DATABASE_URL = "postgresql://postgres:secretpassword@db:5432/northwind"

engine = create_engine(DATABASE_URL)

def get_database_schema() -> str:
    """Fetches all table names and their column definitions, formatted for strict PostgreSQL."""
    schema_info = ""
    try:
        with engine.connect() as conn:
            tables_query = text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
            """)
            tables = conn.execute(tables_query).fetchall()
            
            for table in tables:
                table_name = table[0]
                # INJECT QUOTES HERE
                schema_info += f'Table: "{table_name}"\n'
                
                columns_query = text("""
                    SELECT column_name, data_type 
                    FROM information_schema.columns 
                    WHERE table_name = :tname
                """)
                columns = conn.execute(columns_query, {"tname": table_name}).fetchall()
                
                for col in columns:
                    # INJECT QUOTES HERE
                    schema_info += f'  - "{col[0]}" ({col[1]})\n'
                schema_info += "\n"
                
        return schema_info
    except Exception as e:
        return f"Error fetching schema: {str(e)}"

def execute_read_only_query(sql_query: str) -> dict:
    """Safely executes a query, forcing quotes and blocking modifications."""
    
    # 1. The Regex Sledgehammer (Force Quotes on Aliases)
    # This specifically finds patterns like c.Country and forces c."Country"
    safe_sql = re.sub(
        r'(?<!")\b([a-zA-Z_][a-zA-Z0-9_]*)\.([a-zA-Z_][a-zA-Z0-9_]*)\b(?!")', 
        r'\1."\2"', 
        sql_query
    )
    
    # 2. Security Guardrail
    forbidden_keywords = ["DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "TRUNCATE"]
    if any(keyword in safe_sql.upper() for keyword in forbidden_keywords):
        return {"error": "Security Violation: Only SELECT queries are allowed."}

    # 3. Execution
    try:
        with engine.connect() as conn:
            result = conn.execute(text(safe_sql))
            keys = result.keys()
            data = [dict(zip(keys, row)) for row in result.fetchall()]
            return {"data": data}
    except SQLAlchemyError as e:
        return {"error": str(e)}