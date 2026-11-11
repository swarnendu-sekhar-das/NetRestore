import sys, os, json
import pickle
sys.path.insert(0, os.getcwd())
from src.data_engineering.pipeline import DataPipeline
from src.retrieval.vector_store import TelecomVectorStore
from src.retrieval.tokenizer import telecom_tokenize
from rank_bm25 import BM25Okapi
import re
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("netrestore")

shared_data_dir = "shared_data"
os.makedirs(shared_data_dir, exist_ok=True)
ledger_path = os.path.join(shared_data_dir, "ingested_files.json")
bm25_path = os.path.join(shared_data_dir, "bm25_index.pkl")

force_reindex = "--force" in sys.argv or os.environ.get("FORCE_REINDEX") == "true"

# 1. Load Ledger
processed_files = set()
if not force_reindex and os.path.exists(ledger_path):
    with open(ledger_path, 'r') as f:
        processed_files = set(json.load(f))

if force_reindex:
    logger.info("Force reindex requested. Processing all documents from scratch.")
else:
    logger.info(f"Loaded ledger: {len(processed_files)} files previously ingested.")

# 2. Run Pipeline
pipeline = DataPipeline(data_dir='data/sops')
new_nodes = pipeline.run(processed_files=processed_files)

if not new_nodes:
    logger.info("No new nodes to ingest. Exiting gracefully.")
    sys.exit(0)

# Extract new filenames to update ledger
new_files = set()
for node in new_nodes:
    if "file_name" in node.metadata:
        new_files.add(node.metadata["file_name"])

# 3. Smart ChromaDB Insertion
try:
    vs = TelecomVectorStore(db_path='chroma_db')
    if force_reindex:
        logger.info("Clearing old ChromaDB collection before re-indexing.")
        vs.reset_collection()
    logger.info(f'Indexing {len(new_nodes)} new chunks into ChromaDB.')
    vs.insert_nodes(new_nodes)

    # 4. Smart BM25 Appending using centralized telecom tokenizer
    old_nodes = []
    old_corpus = []

    if not force_reindex and os.path.exists(bm25_path):
        logger.info("Loading historical BM25 data to append new chunks.")
        with open(bm25_path, 'rb') as f:
            data = pickle.load(f)
            old_nodes = data.get("nodes", [])
            old_corpus = data.get("corpus", [])
            
            # If corpus wasn't saved in a previous version, we must rebuild it from old nodes
            if not old_corpus and old_nodes:
                logger.info("Re-tokenizing historical nodes (Legacy index detected).")
                old_corpus = [telecom_tokenize(node.get_content()) for node in old_nodes]

    logger.info(f"Tokenizing {len(new_nodes)} new chunks.")
    new_corpus = [telecom_tokenize(node.get_content()) for node in new_nodes]

    combined_nodes = old_nodes + new_nodes
    combined_corpus = old_corpus + new_corpus

    logger.info("Recomputing BM25 matrix on combined corpus...")
    bm25 = BM25Okapi(combined_corpus)

    # 5. Save State
    with open(bm25_path, 'wb') as f:
        pickle.dump({"bm25": bm25, "nodes": combined_nodes, "corpus": combined_corpus}, f)

    processed_files.update(new_files)
    with open(ledger_path, 'w') as f:
        json.dump(list(processed_files), f, indent=4)

    logger.info(f"Successfully appended {len(new_nodes)} chunks. Total nodes: {len(combined_nodes)}.")
    logger.info("Ingestion complete.")
except Exception as e:
    logger.error(f"Ingestion failed: {e}. Ledger NOT updated — files will be retried on next run.")
    raise
