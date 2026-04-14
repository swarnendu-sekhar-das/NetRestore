#!/bin/bash
set -e

echo "--- Starting Telecom RAG Startup Sequence ---"

# Check if ChromaDB exists and has data
# We look for the 'chroma.sqlite3' file which indicates a persistent DB exists.
DB_PATH="/app/chroma_db/chroma.sqlite3"

if [ ! -f "$DB_PATH" ] || [ "$FORCE_DB_REBUILD" = "true" ]; then
    if [ "$FORCE_DB_REBUILD" = "true" ]; then
        echo "🔄  FORCE_DB_REBUILD is set. Clearing existing database contents..."
        # Safely delete contents but keep the mount-point directory
        rm -rf /app/chroma_db/* /app/chroma_db/.* 2>/dev/null || true
    fi
    echo "⚠️  Vector Database not found or rebuild requested."
    echo "🛠️  Starting automatic data ingestion pipeline..."
    
    # Run the ingestion script. 
    # We use python -m to avoid path issues inside the container.
    export PYTHONPATH=$PYTHONPATH:/app
    python3 notebooks/test_retrieval.py
    
    echo "✅ Data ingestion complete."
else
    echo "🚀 Vector Database found. Skipping ingestion."
fi

echo "🎯 Launching Streamlit Application..."

# Execute the streamlit app, passing through all arguments
exec streamlit run src/app/main.py \
    --server.port=8501 \
    --server.address=0.0.0.0 \
    --server.headless=true
