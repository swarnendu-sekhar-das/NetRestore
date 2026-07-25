"""Run a local ingestion and hybrid-retrieval smoke test."""
import sys
import os

# Add the project root so the src package can be imported.
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.data_engineering.pipeline import DataPipeline
from src.retrieval.vector_store import TelecomVectorStore
from src.retrieval.hybrid_search import TelecomHybridRetriever


def main():
    print("Loading and chunking SOP data.")
    data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "sops"))
    pipeline = DataPipeline(data_dir=data_dir)
    nodes = pipeline.run()

    # Skip chunks that contain no text.
    clean_nodes = [n for n in nodes if n.get_content().strip()]

    print("Initializing the vector store.")
    db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "chroma_db"))

    # Clear the old local test database before running this script.
    if os.path.exists(db_path):
        print(f"Clearing contents of old DB at {db_path} for clean test...")
        for filename in os.listdir(db_path):
            file_path = os.path.join(db_path, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    import shutil
                    shutil.rmtree(file_path)
            except Exception as e:
                print(f"Failed to delete {file_path}. Reason: {e}")

    vs_manager = TelecomVectorStore(db_path=db_path)

    # Embed the chunks and store them in ChromaDB.
    vs_manager.insert_nodes(clean_nodes)

    print("Testing hybrid retrieval.")
    retriever = TelecomHybridRetriever(vector_store_manager=vs_manager, similarity_top_k=10)

    queries = [
        {
            "prompt": "How do I fix optical Rx loss on my Nokia router?",
            "filters": {"equipment_vendor": "Nokia"},
        },
        {
            "prompt": "What is the procedure for BGP neighbor flapping on an Ericsson device?",
            "filters": {"equipment_vendor": "Ericsson"},
        },
        {
            "prompt": "How to resolve OSPF adjacency failure?",
            "filters": {"equipment_vendor": "Juniper"},
        },
        {
            "prompt": "Procedure to clear ALARM_CODE_404",
            "filters": {"equipment_vendor": "Nokia", "alarm_code": "404"},
        },
    ]

    for q in queries:
        print(f"Query: '{q['prompt']}'. Filters: {q['filters']}")
        results = retriever.search(query=q["prompt"], filters=q["filters"])

        if not results:
            print("Warning: No results returned.")
            continue

        for i, node_with_score in enumerate(results):
            score = node_with_score.score
            node = node_with_score.node
            print(f"Result {i + 1}. Reranker score: {score:.4f}.")
            print(f"Title or header: {node.metadata.get('header_path', 'No Header')}")
            preview = node.get_content()[:150].replace("\n", " ")
            print(f"Content: {preview}")
            print(f"Metadata: {node.metadata}")

    print("Integration test complete.")


if __name__ == "__main__":
    main()
