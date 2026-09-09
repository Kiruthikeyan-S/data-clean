"""
DataFlow Application Runner
Starts the backend FastAPI server which serves both the API endpoints and the built frontend UI.
"""
import uvicorn

if __name__ == "__main__":
    print("=======================================================")
    print("   DataFlow — Clean, Validated Structured Data Tool")
    print("   Server running at: http://localhost:8000")
    print("   API Docs:          http://localhost:8000/docs")
    print("=======================================================")
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True)
