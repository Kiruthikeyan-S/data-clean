import os
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from backend.routes.process import router as process_router

app = FastAPI(
    title="DataFlow API",
    description="Backend pipeline for structured and unstructured data cleaning, normalization, and validation.",
    version="1.0.0"
)

# Configure CORS for local development and integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Process router
app.include_router(process_router)

@app.get("/health")
@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "DataFlow Data Processing Engine",
        "version": "1.0.0"
    }

@app.post("/extract")
@app.post("/api/extract")
async def extract_endpoint(request: Request):
    from backend.pipeline import process_file_pipeline
    content_type = request.headers.get("content-type", "")
    if "multipart/form-data" in content_type:
        form = await request.form()
        uploaded_file = form.get("file")
        if uploaded_file and hasattr(uploaded_file, "filename") and uploaded_file.filename:
            file_bytes = await uploaded_file.read()
            return process_file_pipeline(
                filename=uploaded_file.filename,
                content_type=uploaded_file.content_type,
                file_bytes=file_bytes
            )
        files = form.getlist("files")
        if files:
            from backend.routes.process import process_batch_files
            return await process_batch_files(files)
    
    # Check JSON or raw body
    body_bytes = await request.body()
    try:
        data = await request.json()
        raw_text = data.get("text") or data.get("content") or str(data)
    except Exception:
        raw_text = body_bytes.decode("utf-8", errors="ignore")
    
    return process_file_pipeline(
        filename="input.txt",
        content_type="text/plain",
        file_bytes=raw_text.encode("utf-8")
    )

# Mount static frontend build if it exists
frontend_dist = Path(__file__).parent.parent / "frontend" / "dist"
if frontend_dist.exists() and (frontend_dist / "index.html").exists():
    app.mount("/assets", StaticFiles(directory=frontend_dist / "assets"), name="assets")
    
    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        file_path = frontend_dist / full_path
        if file_path.exists() and file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(frontend_dist / "index.html")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
