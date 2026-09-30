# ==========================================
# Multi-Stage Dockerfile for DataFlow
# 1. Builds Frontend (React + Vite + TS)
# 2. Sets up Python Backend (FastAPI)
# ==========================================

# --- Stage 1: Build React Frontend ---
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend

COPY frontend/package*.json ./
RUN npm ci

COPY frontend/ ./
RUN npm run build

# --- Stage 2: Python Backend & Production Runner ---
FROM python:3.11-slim AS runner
WORKDIR /app

# Install system dependencies if required for PyMuPDF/Pillow
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code and runner
COPY backend/ ./backend/
COPY run.py .

# Copy built frontend assets into frontend/dist for FastAPI static file serving
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# Expose default port
EXPOSE 8000

ENV PORT=8000
ENV PYTHONUNBUFFERED=1

# Run FastAPI server
CMD ["sh", "-c", "uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
