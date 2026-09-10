from fastapi import APIRouter
from db.fts_search import search, get_all_sessions
from models.schemas import SearchResult

router = APIRouter()

@router.get("/history")
async def get_history():
    results = get_all_sessions()
    return {"results": results, "query": "", "total": len(results)}

@router.get("/search", response_model=SearchResult)
async def search_history(q: str = ""):
    if not q.strip():
        results = get_all_sessions()
    else:
        results = search(q)
    return SearchResult(results=results, query=q, total=len(results))
