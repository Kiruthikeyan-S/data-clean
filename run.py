"""
DataFlow Application Runner
Starts the backend FastAPI server which serves both the API endpoints and the built frontend UI.
"""
import os
import uvicorn

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    host = os.environ.get("HOST", "0.0.0.0")
    
    print("=======================================================")
    print("   DataFlow — Clean, Validated Structured Data Tool")
    print(f"   Server running at: http://{host}:{port}")
    print(f"   API Docs:          http://{host}:{port}/docs")
    print("=======================================================")
    uvicorn.run("backend.main:app", host=host, port=port, reload=False)

