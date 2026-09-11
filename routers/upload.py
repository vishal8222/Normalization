from fastapi import APIRouter, UploadFile, File, HTTPException
import uuid
import os
import config
from models.schemas import UploadResponse
from engine.parser import parse_csv, parse_excel, parse_pdf
from engine.dependency import FunctionalDependencyAnalyzer
from typing import Dict, Any

router = APIRouter()

# Global sessions dict to store uploaded data
sessions: Dict[str, dict] = {}

@router.post("/upload", response_model=UploadResponse)
async def upload_file(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    file_ext = os.path.splitext(file.filename)[1].lower()
    
    # Save file to UPLOAD_DIR
    os.makedirs(config.UPLOAD_DIR, exist_ok=True)
    file_path = os.path.join(config.UPLOAD_DIR, file.filename)
    
    with open(file_path, "wb") as f:
        f.write(await file.read())

    # Parse file based on extension
    if file_ext == ".csv":
        columns, rows = parse_csv(file_path)
    elif file_ext in [".xlsx", ".xls"]:
        columns, rows = parse_excel(file_path)
    elif file_ext == ".pdf":
        columns, rows = parse_pdf(file_path)
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported file extension: {file_ext}")

    session_id = str(uuid.uuid4())
    
    sessions[session_id] = {
        "filename": file.filename,
        "columns": columns,
        "rows": rows,
        "file_type": file_ext
    }
    sample_data = rows[:5] if len(rows) > 5 else rows

    # Auto-detect dependencies & potential primary keys
    suggested_deps = FunctionalDependencyAnalyzer.auto_detect_dependencies(columns, rows)
    
    # Filter suggested dependencies to non-trivial ones (exclude if determinant is unique for every row, e.g., surrogate key)
    # A candidate key has unique values for each row:
    unique_cols = [c for c in columns if len(set(r.get(c) for r in rows if r.get(c))) == len(rows)]
    
    # Filter out determinants that are full row keys (e.g. RecordID) so we focus on business FDs
    meaningful_deps = []
    for d in suggested_deps:
        det_col = d.determinant[0]
        if det_col not in unique_cols or len(unique_cols) == len(columns):
            meaningful_deps.append(d)

    # Best guess for composite/primary key:
    # If there's an OrderID and ProductID pattern or similar composite, or unique_cols
    suggested_pk = []
    if "OrderID" in columns and "ProductID" in columns:
        suggested_pk = ["OrderID", "ProductID"]
    elif "StudentID" in columns and "Courses" in columns:
        suggested_pk = ["StudentID", "Courses"]
    elif unique_cols:
        suggested_pk = [unique_cols[0]]
    elif columns:
        suggested_pk = [columns[0]]

    return UploadResponse(
        session_id=session_id,
        columns=columns,
        row_count=len(rows),
        sample_data=sample_data,
        suggested_dependencies=meaningful_deps,
        suggested_primary_key=suggested_pk
    )
