#!/bin/bash
set -e

echo "Starting NetRestore."

# ChromaDB creates chroma.sqlite3 after the first write.
DB_PATH="/app/chroma_db/chroma.sqlite3"

if [ ! -f "$DB_PATH" ] || [ "$FORCE_DB_REBUILD" = "true" ]; then
    if [ "$FORCE_DB_REBUILD" = "true" ]; then
        echo "Rebuilding the vector database because FORCE_DB_REBUILD is true."
        # Delete only the database contents, not the directory itself.
        find /app/chroma_db -mindepth 1 -delete 2>/dev/null || true
    fi
    echo "The vector database is missing or needs to be rebuilt."
    echo "Starting data ingestion."

    # Let the inline Python code import the application package.
    export PYTHONPATH=/app

    # Build the application database from the SOP corpus.
    python3 -c "
import sys
sys.path.insert(0, '/app')
from src.data_engineering.pipeline import DataPipeline
from src.retrieval.vector_store import TelecomVectorStore

print('Loading and chunking SOP documents.')
pipeline = DataPipeline(data_dir='/app/data/sops')
nodes = pipeline.run()

if not nodes:
    print('ERROR: No nodes produced. Check that /app/data contains SOP documents.')
    sys.exit(1)

print(f'Indexing {len(nodes)} chunks into ChromaDB.')
vs = TelecomVectorStore(db_path='/app/chroma_db')
vs.insert_nodes(nodes)
print('Ingestion complete.')
"

    echo "Data ingestion complete."
else
    echo "Existing vector database found. Skipping ingestion."
fi

echo "Starting the Streamlit application."

# Replace this shell with the Streamlit process.
exec streamlit run src/app/main.py \
    --server.port=8501 \
    --server.address=0.0.0.0 \
    --server.headless=true
