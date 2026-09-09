import io
import json
import pandas as pd
from fastapi import APIRouter, UploadFile, File, HTTPException, Response
from fastapi.responses import StreamingResponse
from backend.models.schemas import ProcessResponse
from backend.pipeline import process_file_pipeline, RESULTS_STORE

router = APIRouter(prefix="/api", tags=["Processing"])

@router.post("/process", response_model=ProcessResponse)
async def process_file(file: UploadFile = File(...)):
    """
    Accepts an uploaded file (CSV, Excel, JSON, Image, PDF, TXT, DOCX, EML),
    processes it through the DataFlow pipeline, and returns clean structured data.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file uploaded.")
    
    file_bytes = await file.read()
    if len(file_bytes) == 0:
        raise HTTPException(status_code=400, detail="The uploaded file is empty.")
    
    # 50MB limit check
    if len(file_bytes) > 50 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File size exceeds maximum limit (50MB).")
    
    try:
        response = process_file_pipeline(
            filename=file.filename,
            content_type=file.content_type,
            file_bytes=file_bytes
        )
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")


@router.get("/result/{task_id}", response_model=ProcessResponse)
async def get_result(task_id: str):
    """
    Retrieves stored processing result by task ID.
    """
    if task_id not in RESULTS_STORE:
        raise HTTPException(status_code=404, detail="Result not found or expired.")
    return RESULTS_STORE[task_id]


@router.get("/export/{task_id}/json")
async def export_json(task_id: str):
    """
    Exports structured data as formatted JSON.
    """
    if task_id not in RESULTS_STORE:
        raise HTTPException(status_code=404, detail="Result not found.")
    
    res = RESULTS_STORE[task_id]
    export_payload = {
        "file_name": res.filename,
        "classification": res.classification,
        "processed_at": time_now_iso(),
        "data": res.structured_data
    }
    
    json_str = json.dumps(export_payload, indent=2, ensure_ascii=False)
    filename = f"{clean_base_name(res.filename)}_clean.json"
    
    return Response(
        content=json_str,
        media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )


@router.get("/export/{task_id}/csv")
async def export_csv(task_id: str):
    """
    Exports structured data as clean CSV.
    """
    if task_id not in RESULTS_STORE:
        raise HTTPException(status_code=404, detail="Result not found.")
    
    res = RESULTS_STORE[task_id]
    df = to_dataframe(res)
    
    stream = io.StringIO()
    df.to_csv(stream, index=False, encoding="utf-8-sig")
    filename = f"{clean_base_name(res.filename)}_clean.csv"
    
    return Response(
        content=stream.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )


@router.get("/export/{task_id}/excel")
async def export_excel(task_id: str):
    """
    Exports structured data as clean Excel spreadsheet.
    """
    if task_id not in RESULTS_STORE:
        raise HTTPException(status_code=404, detail="Result not found.")
    
    res = RESULTS_STORE[task_id]
    df = to_dataframe(res)
    
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Cleaned Data")
    output.seek(0)
    
    filename = f"{clean_base_name(res.filename)}_clean.xlsx"
    
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )


def to_dataframe(res: ProcessResponse) -> pd.DataFrame:
    """Helper to convert result structured data or fields into a clean DataFrame."""
    if res.classification == "structured" and isinstance(res.structured_data, list):
        return pd.DataFrame(res.structured_data)
    elif res.fields:
        rows = []
        for f in res.fields:
            rows.append({
                "Field": f.label,
                "Value": f.value if f.value is not None else "",
                "Raw Value": f.raw_value if f.raw_value is not None else "",
                "Type": f.field_type
            })
        return pd.DataFrame(rows)
    elif isinstance(res.structured_data, dict):
        return pd.DataFrame([res.structured_data])
    else:
        return pd.DataFrame([{"data": "No structured content"}])


def clean_base_name(filename: str) -> str:
    from pathlib import Path
    return Path(filename).stem


def time_now_iso() -> str:
    import datetime
    return datetime.datetime.now(datetime.timezone.utc).isoformat()
