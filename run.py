"""
DataFlow Application Runner
Starts the backend FastAPI server which serves both the API endpoints and the built frontend UI.
"""
import os
import uvicorn

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    host = os.environ.get("HOST", "0.0.0.0" if os.environ.get("PORT") else "127.0.0.1")
    is_reload = not bool(os.environ.get("PORT"))
    
    print("=======================================================")
    print("   DataFlow — Clean, Validated Structured Data Tool")
    print(f"   Server running at: http://{host}:{port}")
    print(f"   API Docs:          http://{host}:{port}/docs")
    print("=======================================================")
    uvicorn.run("backend.main:app", host=host, port=port, reload=is_reload)

