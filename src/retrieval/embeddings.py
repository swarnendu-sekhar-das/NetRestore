from llama_index.embeddings.huggingface import HuggingFaceEmbedding

def get_embedding_model():
    """Return the local all-MiniLM-L6-v2 embedding model."""
    # This smaller local model keeps memory use manageable for the project.
    embed_model = HuggingFaceEmbedding(model_name="all-MiniLM-L6-v2")
    
    return embed_model
