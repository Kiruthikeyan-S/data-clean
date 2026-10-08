"""
DataFlow Application Runner
Starts the backend FastAPI server which serves both the API endpoints and the built frontend UI.
"""
import os
import sys
import argparse
import uvicorn

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="DataFlow Server Runner")
    parser.add_argument("--port", "-p", type=int, default=int(os.environ.get("PORT", 8080)), help="Port to run the server on (default: 8080)")
    parser.add_argument("--host", "-H", type=str, default=os.environ.get("HOST", "127.0.0.1"), help="Host IP to bind (default: 127.0.0.1)")
    
    # Handle simple positional port (e.g. python run.py 8080)
    args, unknown = parser.parse_known_args()
    if unknown and unknown[0].isdigit():
        args.port = int(unknown[0])

    port = args.port
    host = args.host
    is_reload = not bool(os.environ.get("PORT"))
    
    print("=======================================================")
    print("   DataFlow — Clean, Validated Structured Data Tool")
    print(f"   Server running at: http://{host}:{port}")
    print(f"   API Docs:          http://{host}:{port}/docs")
    print("=======================================================")
    uvicorn.run("backend.main:app", host=host, port=port, reload=is_reload)


