#!/bin/bash
set -e

echo "Running data ingestion..."
# Ensure python path is set to find src
export PYTHONPATH=/app
python scripts/ingest_data.py

echo "Starting FastAPI backend..."
exec uvicorn src.api.main:app --host 0.0.0.0 --port 8000
