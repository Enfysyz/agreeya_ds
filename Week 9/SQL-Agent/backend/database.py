import re
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

# Connect to the PostgreSQL container over the Docker network
# 'postgres' is the user, 'secretpassword' is the password, 'db' is the container name
DATABASE_URL = "postgresql://postgres:secretpassword@db:5432/northwind"

engine = create_engine(DATABASE_URL)

def get_database_schema() -> str:
    """Fetches tables, columns, and Key info (PK/FK) for the LLM."""
    schema_info = ""
    try:
        with engine.connect() as conn:
            # 1. Get all public tables
            tables_query = text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
            """)
            tables = conn.execute(tables_query).fetchall()
            
            for table in tables:
                table_name = table[0]
                schema_info += f'Table: "{table_name}"\n'
                
                # 2. Get constraint info for this specific table (PK and FK)
                # This query finds the column and what kind of key it is
                key_query = text("""
                    SELECT 
                        kcu.column_name, 
                        tc.constraint_type
                    FROM information_schema.table_constraints AS tc 
                    JOIN information_schema.key_column_usage AS kcu
                      ON tc.constraint_name = kcu.constraint_name
                      AND tc.table_schema = kcu.table_schema
                    WHERE tc.table_name = :tname 
                      AND tc.constraint_type IN ('PRIMARY KEY', 'FOREIGN KEY')
                """)
                keys = conn.execute(key_query, {"tname": table_name}).fetchall()
                # Create a dictionary for quick lookup: {column_name: type}
                key_map = {row[0]: row[1] for row in keys}

                # 3. Get column details
                columns_query = text("""
                    SELECT column_name, data_type 
                    FROM information_schema.columns 
                    WHERE table_name = :tname
                """)
                columns = conn.execute(columns_query, {"tname": table_name}).fetchall()
                
                for col in columns:
                    col_name = col[0]
                    col_type = col[1]
                    
                    # Determine suffix if it's a key
                    key_suffix = ""
                    if col_name in key_map:
                        if key_map[col_name] == 'PRIMARY KEY':
                            key_suffix = " [PK]"
                        elif key_map[col_name] == 'FOREIGN KEY':
                            key_suffix = " [FK]"
                    
                    schema_info += f'  - "{col_name}" ({col_type}){key_suffix}\n'
                
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