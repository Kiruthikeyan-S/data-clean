import io
import json
import time
import uuid
from typing import List
import pandas as pd
from fastapi import APIRouter, UploadFile, File, HTTPException, Response
from fastapi.responses import StreamingResponse
from backend.models.schemas import ProcessResponse, BatchProcessResponse
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


# In-memory storage for results and exports
BATCH_RESULTS_STORE: dict = {}


@router.post("/process-batch", response_model=BatchProcessResponse)
async def process_batch_files(files: List[UploadFile] = File(...)):
    """
    Accepts multiple uploaded files simultaneously (e.g. Store, Item, Customer files or multiple receipts),
    cleans all files in parallel, performs cross-file entity resolution, stamps shared entity_id,
    and returns linked clean datasets with a relationship index.
    """
    if not files or len(files) == 0:
        raise HTTPException(status_code=400, detail="No files uploaded.")
        
    start_time = time.time()
    batch_id = str(uuid.uuid4())
    results: List[ProcessResponse] = []
    
    for file in files:
        if not file.filename:
            continue
        file_bytes = await file.read()
        if len(file_bytes) == 0:
            continue
            
        try:
            res = process_file_pipeline(
                filename=file.filename,
                content_type=file.content_type,
                file_bytes=file_bytes
            )
            results.append(res)
        except Exception as e:
            print(f"Error processing batch file {file.filename}: {e}")
            
    if not results:
        raise HTTPException(status_code=400, detail="None of the uploaded batch files could be processed.")
        
    # Cross-File Record Linkage & Entity Resolution
    from backend.matching.cross_file_linker import link_batch_records
    results, relationship_index = link_batch_records(results)

    total_time = round((time.time() - start_time) * 1000, 2)
    batch_response = BatchProcessResponse(
        batch_id=batch_id,
        total_files=len(results),
        results=results,
        relationship_index=relationship_index,
        total_entities_linked=relationship_index.get("total_entities_linked", 0),
        processing_time_ms=total_time
    )
    BATCH_RESULTS_STORE[batch_id] = batch_response
    return batch_response


@router.get("/batch/{batch_id}/export/excel")
async def export_batch_excel(batch_id: str):
    """
    Exports all batch datasets into a single multi-sheet Excel workbook
    containing one sheet per cleaned dataset plus a 'Relationships & Links' sheet.
    """
    if batch_id not in BATCH_RESULTS_STORE:
        raise HTTPException(status_code=404, detail="Batch result not found.")

    batch = BATCH_RESULTS_STORE[batch_id]
    output = io.BytesIO()

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        for idx, res in enumerate(batch.results):
            raw_title = clean_base_name(res.filename) or f"Dataset_{idx + 1}"
            sheet_title = raw_title[:28]
            df = to_dataframe(res)
            df.to_excel(writer, index=False, sheet_name=sheet_title)

        rel_index = batch.relationship_index or {}
        entities = rel_index.get("entities", [])
        if entities:
            rel_rows = []
            for ent in entities:
                rel_rows.append({
                    "Entity ID": ent.get("entity_id"),
                    "Display Name": ent.get("display_name"),
                    "Primary Match Key": ent.get("primary_match_key"),
                    "Files Linked": ", ".join(ent.get("files_involved", [])),
                    "Records Count": ent.get("records_count"),
                    "Is Cross-File": "Yes" if ent.get("is_cross_file") else "No"
                })
            rel_df = pd.DataFrame(rel_rows)
            rel_df.to_excel(writer, index=False, sheet_name="Relationships & Links")

    output.seek(0)
    filename = f"batch_{batch_id[:8]}_linked_datasets.xlsx"

    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )


@router.get("/batch/{batch_id}/export/json")
async def export_batch_json(batch_id: str):
    """
    Exports all batch datasets with their tagged entity_id and the relationship_index as structured JSON.
    """
    if batch_id not in BATCH_RESULTS_STORE:
        raise HTTPException(status_code=404, detail="Batch result not found.")

    batch = BATCH_RESULTS_STORE[batch_id]
    payload = {
        "batch_id": batch.batch_id,
        "total_files": batch.total_files,
        "total_entities_linked": batch.total_entities_linked,
        "relationship_index": batch.relationship_index,
        "datasets": [
            {
                "filename": r.filename,
                "file_type": r.file_type,
                "records_count": len(r.structured_data) if isinstance(r.structured_data, list) else 1,
                "data": r.structured_data
            }
            for r in batch.results
        ]
    }

    json_str = json.dumps(payload, indent=2, ensure_ascii=False)
    filename = f"batch_{batch_id[:8]}_linked_export.json"

    return Response(
        content=json_str,
        media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )


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


@router.get("/export/{task_id}/pdf")
async def export_pdf(task_id: str):
    """
    Exports structured data as a clean, professionally formatted PDF document.
    """
    if task_id not in RESULTS_STORE:
        raise HTTPException(status_code=404, detail="Result not found.")
    
    res = RESULTS_STORE[task_id]
    df = to_dataframe(res)
    
    output = io.BytesIO()
    from reportlab.lib.pagesizes import letter, landscape, portrait
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
    
    pagesize = landscape(letter) if len(df.columns) > 4 else portrait(letter)
    doc = SimpleDocTemplate(
        output,
        pagesize=pagesize,
        rightMargin=24,
        leftMargin=24,
        topMargin=24,
        bottomMargin=24
    )
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'ReportTitle',
        parent=styles['Heading1'],
        fontSize=16,
        textColor=colors.HexColor('#0F172A'),
        spaceAfter=4
    )
    sub_style = ParagraphStyle(
        'ReportSubtitle',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.HexColor('#64748B'),
        spaceAfter=12
    )
    cell_style = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontSize=8,
        leading=10,
        textColor=colors.HexColor('#1E293B')
    )
    header_style = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontSize=8,
        leading=10,
        fontName='Helvetica-Bold',
        textColor=colors.whitesmoke
    )
    
    elements = []
    
    base_name = clean_base_name(res.filename)
    elements.append(Paragraph(f"Cleaned Dataset Report: {base_name}", title_style))
    entity_label = res.entity_info.entity_type.upper() if res.entity_info else "GENERAL"
    elements.append(Paragraph(f"Entity: {entity_label} | Format: {res.file_type.upper()} | Cleaned Records: {len(df)} | Exported: {time_now_iso()[:10]}", sub_style))
    elements.append(Spacer(1, 6))
    
    headers = [Paragraph(str(col).replace('_', ' ').title(), header_style) for col in df.columns]
    table_data = [headers]
    
    for _, row in df.head(500).iterrows():
        row_cells = []
        for val in row:
            v_str = "" if pd.isna(val) or val is None else str(val)
            row_cells.append(Paragraph(v_str, cell_style))
        table_data.append(row_cells)
        
    t = Table(table_data, repeatRows=1)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2563EB')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8FAFC')]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
    ]))
    
    elements.append(t)
    doc.build(elements)
    output.seek(0)
    
    filename = f"{base_name}_clean.pdf"
    return StreamingResponse(
        output,
        media_type="application/pdf",
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


@router.post("/rag/match")
async def rag_entity_match(payload: dict):
    """
    Accepts a single entity record (e.g. new customer, store, item),
    performs isolated Vector RAG search on historical data, generates Groq LLM semantic reasoning,
    and runs deterministic record matching validation.
    """
    from backend.matching.record_matcher import find_rag_matches_for_record
    
    query_record = payload.get("record", {})
    entity_type = payload.get("entity_type", "customer")
    top_k = payload.get("top_k", 5)

    if not query_record:
        raise HTTPException(status_code=400, detail="Payload must include 'record' dictionary.")

    result = find_rag_matches_for_record(
        query_record=query_record,
        entity_type=entity_type,
        top_k=top_k
    )
    return result


@router.post("/rag/schema-lookup")
async def rag_schema_lookup(payload: dict):
    """
    Accepts unfamiliar column headers, queries the Schema Knowledge Base RAG,
    and returns matching canonical schema target fields with explanations.
    """
    from backend.rag.schema_retriever import retrieve_batch_schema_mappings
    
    columns = payload.get("columns", [])
    entity_type = payload.get("entity_type", "general")

    if not columns:
        raise HTTPException(status_code=400, detail="Payload must include 'columns' list.")

    mappings = retrieve_batch_schema_mappings(columns=columns, entity_type=entity_type)
    return {"entity_type": entity_type, "mappings": mappings}


@router.post("/rag/ingest")
async def rag_ingest_records(payload: dict):
    """
    Ingests records into the isolated entity Vector Database knowledge base.
    """
    from backend.rag.record_retriever import ingest_records_batch
    
    records = payload.get("records", [])
    entity_type = payload.get("entity_type", "customer")

    if not records:
        raise HTTPException(status_code=400, detail="Payload must include 'records' list.")

    count = ingest_records_batch(records=records, entity_type=entity_type)
    return {"status": "success", "ingested_count": count, "entity_type": entity_type}

