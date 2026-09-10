from typing import List
from models.schemas import TableInfo

def _map_type_to_mysql(sqlite_type: str) -> str:
    sqlite_type = sqlite_type.upper()
    if 'INT' in sqlite_type:
        return 'INT'
    if 'CHAR' in sqlite_type or 'TEXT' in sqlite_type:
        return 'VARCHAR(255)'
    if 'REAL' in sqlite_type or 'FLOA' in sqlite_type or 'DOUB' in sqlite_type:
        return 'DOUBLE'
    return 'VARCHAR(255)'

def generate_mysql_ddl(tables: List[TableInfo]) -> str:
    ddl_statements = []
    
    for table in tables:
        lines = []
        lines.append(f"CREATE TABLE {table.name} (")
        
        col_defs = []
        for col in table.columns:
            col_type = _map_type_to_mysql(col.data_type)
            constraints = []
            if col.is_primary_key:
                constraints.append("PRIMARY KEY")
            
            col_def = f"    {col.name} {col_type}"
            if constraints:
                col_def += " " + " ".join(constraints)
            col_defs.append(col_def)
            
        lines.append(",\n".join(col_defs))
        lines.append(");\n")
        ddl_statements.append("\n".join(lines))
        
    return "\n".join(ddl_statements)

def generate_oracle_ddl(tables: List[TableInfo]) -> str:
    ddl_statements = []
    
    for table in tables:
        lines = []
        lines.append(f"CREATE TABLE {table.name} (")
        
        col_defs = []
        for col in table.columns:
            col_type = _map_type_to_mysql(col.data_type).replace('VARCHAR', 'VARCHAR2')
            constraints = []
            if col.is_primary_key:
                constraints.append("PRIMARY KEY")
                
            col_def = f"    {col.name} {col_type}"
            if constraints:
                col_def += " " + " ".join(constraints)
            col_defs.append(col_def)
            
        lines.append(",\n".join(col_defs))
        lines.append(");\n")
        ddl_statements.append("\n".join(lines))
        
    return "\n".join(ddl_statements)
