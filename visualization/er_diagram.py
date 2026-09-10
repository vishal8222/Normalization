from typing import List, Dict, Any
from models.schemas import TableInfo

def generate_er_data(tables: List[TableInfo]) -> Dict[str, Any]:
    nodes = []
    edges = []
    
    for table in tables:
        nodes.append({
            "id": table.name,
            "columns": [c.name for c in table.columns],
            "primary_key": [c.name for c in table.columns if c.is_primary_key]
        })
        
        for col in table.columns:
            if col.is_foreign_key and col.references:
                # Basic parsing assuming format 'other_table.col' or just 'other_table'
                ref_parts = col.references.split('.')
                ref_table = ref_parts[0]
                ref_col = ref_parts[1] if len(ref_parts) > 1 else ""
                
                edges.append({
                    "from": table.name,
                    "to": ref_table,
                    "from_col": col.name,
                    "to_col": ref_col,
                    "type": "1:N"  # Default assumption for simplicity
                })
                
    return {
        "nodes": nodes,
        "edges": edges
    }
