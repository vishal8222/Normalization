import sqlite3
import os
from typing import List, Dict, Any, Tuple
from config import SESSIONS_DIR

class SQLiteEngine:
    def __init__(self):
        pass

    def create_session_db(self, session_id: str) -> sqlite3.Connection:
        db_path = SESSIONS_DIR / f"{session_id}.db"
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def execute_and_log(self, conn: sqlite3.Connection, sql: str, params: tuple = None) -> List[Dict[str, Any]]:
        cursor = conn.cursor()
        if params:
            cursor.execute(sql, params)
        else:
            cursor.execute(sql)
        conn.commit()
        
        if cursor.description:
            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            return [{col: row[i] for i, col in enumerate(columns)} for row in rows]
        return []

    def load_data(self, conn: sqlite3.Connection, table_name: str, columns: List[str], rows: List[Dict[str, Any]]):
        if not columns or not rows:
            return
            
        # CREATE TABLE
        cols_def = ", ".join([f'"{col}" TEXT' for col in columns])
        create_sql = f'CREATE TABLE IF NOT EXISTS "{table_name}" ({cols_def});'
        self.execute_and_log(conn, create_sql)
        
        # INSERT
        placeholders = ", ".join(["?"] * len(columns))
        insert_sql = f'INSERT INTO "{table_name}" ({", ".join([f"{c}" for c in columns])}) VALUES ({placeholders});'
        
        cursor = conn.cursor()
        for row in rows:
            params = tuple(row.get(col) for col in columns)
            cursor.execute(insert_sql, params)
        conn.commit()

    def get_table_data(self, conn: sqlite3.Connection, table_name: str) -> List[Dict[str, Any]]:
        return self.execute_and_log(conn, f'SELECT * FROM "{table_name}";')

    def get_table_info(self, conn: sqlite3.Connection, table_name: str) -> List[Dict[str, Any]]:
        # Using PRAGMA table_info to get column info
        return self.execute_and_log(conn, f'PRAGMA table_info("{table_name}");')
