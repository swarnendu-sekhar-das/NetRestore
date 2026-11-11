#!/bin/bash
set -e

echo "Starting NetRestore local environment."

export PYTHONPATH=$(pwd)
bash scripts/startup.sh &
BACKEND_PID=$!

# Clean up background backend process when Streamlit exits or is interrupted
trap "echo 'Stopping backend process (PID: $BACKEND_PID)...'; kill -TERM $BACKEND_PID 2>/dev/null || true" EXIT INT TERM

echo "Starting the Streamlit application."
python3 -m streamlit run src/app/main.py \
    --server.port=8501 \
    --server.address=0.0.0.0 \
    --server.headless=true
