#!/bin/bash
set -e

echo "Starting NetRestore local environment."

export PYTHONPATH=$(pwd)
bash scripts/startup.sh &
BACKEND_PID=$!

echo "Starting the Streamlit application."
# Replace this shell with the Streamlit process.
exec python3 -m streamlit run src/app/main.py \
    --server.port=8501 \
    --server.address=0.0.0.0 \
    --server.headless=true
