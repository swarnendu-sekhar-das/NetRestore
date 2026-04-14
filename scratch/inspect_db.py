import chromadb
import os

db_path = "/Users/swarnendusekhardas/SSD_Files/Workspace/SPE Major Project/chroma_db"
if not os.path.exists(db_path):
    print("DB not found")
else:
    client = chromadb.PersistentClient(path=db_path)
    collection = client.get_collection("telecom_sops")
    # Get a sample of documents and their metadata
    results = collection.get(limit=10)
    for i in range(len(results['ids'])):
        print(f"ID: {results['ids'][i]}")
        print(f"Metadata: {results['metadatas'][i]}")
        print(f"Content Preview: {results['documents'][i][:100]}...")
        print("-" * 20)
