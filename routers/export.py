from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, Response
from export.excel_export import ExcelExporter
from export.pdf_export import PdfExporter
from routers.upload import sessions
from models.schemas import NormalizationResult
import os
import config

router = APIRouter()

@router.get("/export/excel/{session_id}")
async def export_excel(session_id: str):
    if session_id not in sessions or "result" not in sessions[session_id]:
        raise HTTPException(status_code=404, detail="Result not found")
        
    result_data = sessions[session_id]["result"]
    result = NormalizationResult(**result_data)
    
    exporter = ExcelExporter(result)
    os.makedirs(config.EXPORT_DIR, exist_ok=True)
    file_path = os.path.join(config.EXPORT_DIR, f"{session_id}.xlsx")
    
    exporter.export(file_path)
    return FileResponse(file_path, filename=f"normalization_report_{session_id}.xlsx", media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

@router.get("/export/pdf/{session_id}")
async def export_pdf(session_id: str):
    if session_id not in sessions or "result" not in sessions[session_id]:
        raise HTTPException(status_code=404, detail="Result not found")
        
    result_data = sessions[session_id]["result"]
    result = NormalizationResult(**result_data)
    
    exporter = PdfExporter(result)
    os.makedirs(config.EXPORT_DIR, exist_ok=True)
    file_path = os.path.join(config.EXPORT_DIR, f"{session_id}.pdf")
    
    exporter.export(file_path)
    return FileResponse(file_path, filename=f"normalization_report_{session_id}.pdf", media_type="application/pdf")

@router.get("/export/sql/{session_id}")
async def export_sql(session_id: str):
    if session_id not in sessions or "result" not in sessions[session_id]:
        raise HTTPException(status_code=404, detail="Result not found")
        
    result_data = sessions[session_id]["result"]
    result = NormalizationResult(**result_data)
    
    sql_content = result.generated_ddl
    
    return Response(
        content=sql_content,
        media_type="application/sql",
        headers={"Content-Disposition": f"attachment; filename=schema_{session_id}.sql"}
    )
