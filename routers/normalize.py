from fastapi import APIRouter, HTTPException, Body
from models.schemas import DependencyRequest, NormalizationResult, FunctionalDependency
from engine.normalizer import DatabaseNormalizer
from db.fts_search import index_session
from routers.upload import sessions
from typing import Dict, Any

router = APIRouter()

@router.post("/dependencies")
async def add_dependencies(req: DependencyRequest):
    if req.session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    sessions[req.session_id]["dependencies"] = [dep.model_dump() for dep in req.dependencies]
    sessions[req.session_id]["primary_key"] = req.primary_key
    
    return {"status": "ok", "session_id": req.session_id}

@router.post("/normalize", response_model=NormalizationResult)
async def normalize_data(payload: Dict[str, str] = Body(...)):
    session_id = payload.get("session_id")
    if not session_id or session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
        
    session_data = sessions[session_id]
    
    columns = session_data.get("columns", [])
    rows = session_data.get("rows", [])
    primary_key = session_data.get("primary_key", [])
    dependencies_raw = session_data.get("dependencies", [])
    dependencies = [FunctionalDependency(**d) if isinstance(d, dict) else d for d in dependencies_raw]
    filename = session_data.get("filename", "unknown")
    
    normalizer = DatabaseNormalizer(session_id)
    result = normalizer.normalize(columns, rows, primary_key, dependencies)
    
    sessions[session_id]["result"] = result.model_dump()
    
    # Index in FTS
    file_type = session_data.get("file_type", "unknown")
    summary = f"Normalized {filename}. Resulting tables: {len(result.final_tables)}"
    index_session(session_id, filename, file_type, columns, summary)
    
    return result

@router.get("/normalize/{session_id}/step/{step}")
async def get_normalization_step(session_id: str, step: str):
    if session_id not in sessions or "result" not in sessions[session_id]:
        raise HTTPException(status_code=404, detail="Result not found")
        
    result = sessions[session_id]["result"]
    
    for step_result in result.get("steps", []):
        if step_result.get("normal_form", "").lower() == step.lower():
            return step_result
            
    raise HTTPException(status_code=404, detail=f"Step {step} not found")
