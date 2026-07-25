import chromadb
from llama_index.core import VectorStoreIndex, StorageContext
from llama_index.vector_stores.chroma import ChromaVectorStore
from src.retrieval.embeddings import get_embedding_model
import os

class TelecomVectorStore:
    """Manage the local ChromaDB collection and its LlamaIndex wrapper."""
    
    def __init__(self, db_path: str = "./chroma_db", collection_name: str = "telecom_sops"):
        self.db_path = db_path
        self.collection_name = collection_name
        self.embed_model = get_embedding_model()
        
        # Open the persistent ChromaDB collection.
        self.db = chromadb.PersistentClient(path=self.db_path)
        self.chroma_collection = self.db.get_or_create_collection(self.collection_name)
        
        # Wrap the collection for LlamaIndex.
        self.vector_store = ChromaVectorStore(chroma_collection=self.chroma_collection)
        self.storage_context = StorageContext.from_defaults(vector_store=self.vector_store)
        
        # Load the index only when it is needed.
        self.index = None

    def insert_nodes(self, nodes):
        """Embed the supplied chunks and store them in ChromaDB."""
        print(f"Indexing {len(nodes)} chunks into ChromaDB at {self.db_path}.")
        self.index = VectorStoreIndex(
            nodes, 
            storage_context=self.storage_context, 
            embed_model=self.embed_model
        )
        print("Indexing complete.")
        
    def get_index(self):
        """Load the existing index if this instance has not created one."""
        if not self.index:
            self.index = VectorStoreIndex.from_vector_store(
                self.vector_store,
                embed_model=self.embed_model
            )
        return self.index
