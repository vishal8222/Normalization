import config
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from routers import upload, normalize, export, history
from db.fts_search import init_fts_db
import uvicorn

app = FastAPI(
    title="Database Normalizer Tool",
    description="Upload denormalized data → Normalize to 1NF/2NF/3NF → Export as Excel/PDF",
    version="1.0.0"
)

# CORS
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# Mount static files and templates
app.mount("/static", StaticFiles(directory=str(config.STATIC_DIR)), name="static")
templates = Jinja2Templates(directory=str(config.TEMPLATES_DIR))

# Include routers
app.include_router(upload.router, prefix="/api", tags=["Upload"])
app.include_router(normalize.router, prefix="/api", tags=["Normalize"])
app.include_router(export.router, prefix="/api", tags=["Export"])
app.include_router(history.router, prefix="/api", tags=["History"])

@app.on_event("startup")
async def startup():
    init_fts_db()

@app.get("/")
async def home(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
