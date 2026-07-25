"""Print a small sample from the local ChromaDB collection for debugging."""

import chromadb
import os

# Local database path used by this helper.
db_path = "/Users/swarnendusekhardas/SSD_Files/Workspace/SPE Major Project/chroma_db"

# Stop if the database has not been created yet.
if not os.path.exists(db_path):
    print("Error: ChromaDB was not found at the configured path.")
    print(f"   Path: {db_path}")
    print("   Please run the data ingestion pipeline first.")
else:
    # Open the local ChromaDB client.
    client = chromadb.PersistentClient(path=db_path)
    
    # Read the telecom SOP collection.
    collection = client.get_collection("telecom_sops")
    
    # Read a small set of documents and their metadata.
    results = collection.get(limit=10)
    
    print("NetRestore ChromaDB inspection results")
    print(f"   Collection: telecom_sops")
    print(f"   Sample Size: {len(results['ids'])} documents")
    
    # Print details for each sample document.
    for i in range(len(results['ids'])):
        print(f"Document {i + 1}:")
        print(f"   ID: {results['ids'][i]}")
        print(f"   Metadata: {results['metadatas'][i]}")
        print(f"Content preview: {results['documents'][i][:100]}")
