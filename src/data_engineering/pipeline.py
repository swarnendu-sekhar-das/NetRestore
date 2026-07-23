import sys
import os

from llama_index.core.schema import TextNode

# Add src to the path so we can import modules
sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))

from src.data_engineering.parser import TelecomDocumentParser
from src.data_engineering.chunking import get_markdown_chunker, get_pdf_chunker, TelecomMetadataExtractor


class DataPipeline:
    def __init__(self, data_dir: str):
        self.parser = TelecomDocumentParser(data_dir=data_dir)
        self.md_chunker = get_markdown_chunker()
        self.pdf_chunker = get_pdf_chunker()
        self.metadata_extractor = TelecomMetadataExtractor()

    def run(self) -> list[TextNode]:
        """
        Runs the data pipeline:
        1. Loads files
        2. Chunks them
        3. Extracts metadata
        """
        print("--- Starting Data Pipeline ---")
        docs = self.parser.load_documents()
        if not docs:
            print("No documents found. Aborting pipeline.")
            return []

        print("Chunking documents...")
        nodes = []
        for doc in docs:
            # Extract vendor from the document text or filename
            doc_vendor = None
            vendors = ["Cisco", "Nokia", "Juniper", "Ericsson", "Huawei", "Arista"]
            # Check first 500 chars or filename
            content_sample = doc.get_content()[:500].lower()
            file_name_info = doc.metadata.get("file_name", "").lower()
            for v in vendors:
                if v.lower() in content_sample or v.lower() in file_name_info:
                    doc_vendor = v
                    break

            # Route to the correct chunker based on file extension
            if file_name_info.endswith(".pdf"):
                doc_nodes = self.pdf_chunker.get_nodes_from_documents([doc])
            else:
                doc_nodes = self.md_chunker.get_nodes_from_documents([doc])
            
            for node in doc_nodes:
                # Extract specific metadata (Alarm codes, etc.)
                metadata = self.metadata_extractor._extract_metadata(node.get_content())
                node.metadata.update(metadata)
                
                # Propagate doc-level vendor if node-level extraction missed it
                if "equipment_vendor" not in node.metadata and doc_vendor:
                    node.metadata["equipment_vendor"] = doc_vendor
                
                # Ensure filename is also in metadata for easier source tracking
                if "file_name" not in node.metadata:
                    node.metadata["file_name"] = doc.metadata.get("file_name", "Unknown")
            
            nodes.extend(doc_nodes)

        print(f"Produced and enriched {len(nodes)} structural chunks.")

        print("--- Data Pipeline Finished ---")
        return nodes
