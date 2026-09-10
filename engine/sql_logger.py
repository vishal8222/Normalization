from typing import List, Dict, Any
from datetime import datetime

class SQLLogger:
    def __init__(self):
        self.queries: List[Dict[str, Any]] = []
        
    def log(self, sql: str, params: tuple = None, step: str = "", description: str = ""):
        self.queries.append({
            "sql": sql,
            "params": params,
            "timestamp": datetime.now().isoformat(),
            "step": step,
            "description": description
        })
        
    def get_all(self) -> List[Dict[str, Any]]:
        return self.queries
        
    def get_by_step(self, step: str) -> List[Dict[str, Any]]:
        return [q for q in self.queries if q.get("step") == step]
        
    def clear(self):
        self.queries = []
