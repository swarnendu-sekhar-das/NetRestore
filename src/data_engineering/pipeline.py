import sys
import os

from llama_index.core.schema import TextNode

import logging

logger = logging.getLogger("netrestore")

# Add the project root so the src package can be imported.
sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))

from src.data_engineering.parser import TelecomDocumentParser
from src.data_engineering.chunking import get_pdf_chunker, TelecomMetadataExtractor


class DataPipeline:
    def __init__(self, data_dir: str):
        self.parser = TelecomDocumentParser(data_dir=data_dir)
        self.pdf_chunker = get_pdf_chunker()
        self.metadata_extractor = TelecomMetadataExtractor()

    def run(self) -> list[TextNode]:
        """Load SOP PDFs, split them into chunks, and add metadata."""
        logger.info("Starting data pipeline.")
        docs = self.parser.load_documents()
        if not docs:
            logger.warning("No documents found. Aborting pipeline.")
            return []

        logger.info("Chunking documents.")
        nodes = []
        for doc in docs:
            # Find the vendor in the document text or filename.
            doc_vendor = None
            vendors = ["Cisco", "Nokia", "Juniper", "Ericsson", "Huawei", "Arista"]
            # Check the first part of the content and the filename.
            content_sample = doc.get_content()[:500].lower()
            file_name_info = doc.metadata.get("file_name", "").lower()
            for v in vendors:
                if v.lower() in content_sample or v.lower() in file_name_info:
                    doc_vendor = v
                    break

            # Only PDF SOPs are allowed in the production corpus.
            if not file_name_info.endswith(".pdf"):
                continue
            doc_nodes = self.pdf_chunker.get_nodes_from_documents([doc])
            
            for node in doc_nodes:
                # Extract alarm, vendor, severity, and node metadata.
                metadata = self.metadata_extractor._extract_metadata(node.get_content())
                node.metadata.update(metadata)
                
                # Use the document vendor when the chunk does not contain one.
                if "equipment_vendor" not in node.metadata and doc_vendor:
                    node.metadata["equipment_vendor"] = doc_vendor
                
                # Keep the filename so the source can be shown later.
                if "file_name" not in node.metadata:
                    node.metadata["file_name"] = doc.metadata.get("file_name", "Unknown")
            
            nodes.extend(doc_nodes)

        logger.info(f"Produced and enriched {len(nodes)} structural chunks.")

        logger.info("Data pipeline finished.")
        return nodes
