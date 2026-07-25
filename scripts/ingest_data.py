import sys, os
sys.path.insert(0, os.getcwd())
from src.data_engineering.pipeline import DataPipeline
from src.retrieval.vector_store import TelecomVectorStore

import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("netrestore")

logger.info('Loading and chunking SOP documents.')
pipeline = DataPipeline(data_dir='data/sops')
nodes = pipeline.run()

if not nodes:
    logger.error('ERROR: No nodes produced. Check that /data contains SOP documents.')
    sys.exit(1)

logger.info(f'Indexing {len(nodes)} chunks into ChromaDB.')
vs = TelecomVectorStore(db_path='chroma_db')
vs.insert_nodes(nodes)
logger.info('Ingestion complete.')
