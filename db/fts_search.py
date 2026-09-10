import sqlite3
from typing import List
from datetime import datetime
from config import FTS_DB_PATH
from models.schemas import HistoryItem

def init_fts_db():
    conn = sqlite3.connect(FTS_DB_PATH)
    conn.execute('''
        CREATE VIRTUAL TABLE IF NOT EXISTS sessions_fts USING fts5(
            session_id, filename, file_type, columns_text, created_at, table_count, status
        );
    ''')
    conn.commit()
    conn.close()

def index_session(session_id: str, filename: str, file_type: str, columns: List[str], summary: str):
    conn = sqlite3.connect(FTS_DB_PATH)
    columns_text = " ".join(columns) + " " + summary
    created_at = datetime.now().isoformat()
    table_count = 1  # Initially 1 for upload
    status = "uploaded"
    
    conn.execute('''
        INSERT INTO sessions_fts (session_id, filename, file_type, columns_text, created_at, table_count, status)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (session_id, filename, file_type, columns_text, created_at, table_count, status))
    conn.commit()
    conn.close()

def search(query: str) -> List[HistoryItem]:
    conn = sqlite3.connect(FTS_DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Simple match against the FTS table
    cursor.execute('''
        SELECT session_id, filename, file_type, created_at, table_count, status
        FROM sessions_fts
        WHERE sessions_fts MATCH ?
        ORDER BY rank
    ''', (f"{query}*",))
    
    results = []
    for row in cursor.fetchall():
        results.append(HistoryItem(
            session_id=row['session_id'],
            filename=row['filename'],
            file_type=row['file_type'],
            created_at=row['created_at'],
            table_count=int(row['table_count']),
            status=row['status']
        ))
    
    conn.close()
    return results

def get_all_sessions() -> List[HistoryItem]:
    conn = sqlite3.connect(FTS_DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT session_id, filename, file_type, created_at, table_count, status
        FROM sessions_fts
        ORDER BY created_at DESC
    ''')
    
    results = []
    for row in cursor.fetchall():
        results.append(HistoryItem(
            session_id=row['session_id'],
            filename=row['filename'],
            file_type=row['file_type'],
            created_at=row['created_at'],
            table_count=int(row['table_count']),
            status=row['status']
        ))
    
    conn.close()
    return results
