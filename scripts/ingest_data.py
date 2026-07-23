import sys, os
sys.path.insert(0, os.getcwd())
from src.data_engineering.pipeline import DataPipeline
from src.retrieval.vector_store import TelecomVectorStore

print('Loading and chunking SOP documents...')
pipeline = DataPipeline(data_dir='data')
nodes = pipeline.run()

if not nodes:
    print('ERROR: No nodes produced. Check that /data contains SOP documents.')
    sys.exit(1)

print(f'Indexing {len(nodes)} chunks into ChromaDB...')
vs = TelecomVectorStore(db_path='chroma_db')
vs.insert_nodes(nodes)
print('✅ Ingestion complete.')
