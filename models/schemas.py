from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime

class ColumnInfo(BaseModel):
    name: str
    data_type: str = "TEXT"
    is_primary_key: bool = False
    is_foreign_key: bool = False
    references: Optional[str] = None  # "table_name(column_name)"

class TableInfo(BaseModel):
    name: str
    columns: List[ColumnInfo]
    data: List[Dict[str, Any]]

class FunctionalDependency(BaseModel):
    determinant: List[str]
    dependent: List[str]

class NormalizationViolation(BaseModel):
    normal_form: str  # "1NF", "2NF", "3NF"
    violation_type: str
    description: str
    affected_columns: List[str]

class NormalizationStepResult(BaseModel):
    normal_form: str
    violations_found: List[NormalizationViolation]
    resulting_tables: List[TableInfo]
    explanation: str
    sql_queries: List[str]

class NormalizationResult(BaseModel):
    session_id: str
    original_table: TableInfo
    steps: List[NormalizationStepResult]  # [1NF, 2NF, 3NF]
    final_tables: List[TableInfo]
    generated_ddl: str
    all_sql_queries: List[str]
    er_diagram_data: Dict[str, Any]  # for visualization

class UploadResponse(BaseModel):
    session_id: str
    columns: List[str]
    row_count: int
    sample_data: List[Dict[str, Any]]

class DependencyRequest(BaseModel):
    session_id: str
    dependencies: List[FunctionalDependency]
    primary_key: List[str]

class HistoryItem(BaseModel):
    session_id: str
    filename: str
    file_type: str
    created_at: str
    table_count: int
    status: str

class SearchResult(BaseModel):
    results: List[HistoryItem]
    query: str
    total: int
