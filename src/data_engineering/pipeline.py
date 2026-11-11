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

    def run(self, processed_files: set = None) -> list[TextNode]:
        """Load SOP PDFs, split them into chunks, and add metadata."""
        logger.info("Starting data pipeline.")
        docs = self.parser.load_documents(processed_files)
        if not docs:
            logger.info("No new documents to process. Aborting pipeline.")
            return []

        logger.info("Chunking documents.")
        from collections import defaultdict
        grouped_docs = defaultdict(list)
        for doc in docs:
            fn = doc.metadata.get("file_name", "unknown")
            grouped_docs[fn].append(doc)

        nodes = []
        for file_name, file_pages in grouped_docs.items():
            file_name_info = file_name.lower()
            if not file_name_info.endswith(".pdf"):
                continue

            # Sort pages if page_label is numeric
            try:
                sorted_pages = sorted(file_pages, key=lambda p: int(p.metadata.get("page_label", "1")))
            except (ValueError, TypeError):
                sorted_pages = file_pages

            full_text = "\n".join([p.get_content() for p in sorted_pages])
            base_meta = sorted_pages[0].metadata.copy()

            # Find the vendor in the document text or filename.
            doc_vendor = None
            vendors = ["Cisco", "Nokia", "Juniper", "Ericsson", "Huawei", "Arista"]
            content_sample = full_text[:1000].lower()
            for v in vendors:
                if v.lower() in content_sample or v.lower() in file_name_info:
                    doc_vendor = v
                    break

            # Extract document-level metadata from full document text and filename
            doc_metadata = self.metadata_extractor._extract_metadata(full_text)
            import re
            # Fallback node_id from filename (e.g., IND-ACC-16_ALARM_3049_SOP.pdf)
            if "node_id" not in doc_metadata:
                fn_node = re.search(r'([A-Za-z]{2,5}-(?:CORE|PE|ACC|AGG|CE|P|RR)-\d{2})', file_name, re.IGNORECASE)
                if fn_node:
                    doc_metadata["node_id"] = fn_node.group(1).upper()

            # Fallback alarm_code from filename
            if "alarm_code" not in doc_metadata:
                fn_alarm = re.search(r'ALARM(?:[_\s-]*(?:CODE)?[_\s-]*)?(\d+)', file_name, re.IGNORECASE)
                if fn_alarm:
                    doc_metadata["alarm_code"] = fn_alarm.group(1)

            if doc_vendor:
                doc_metadata["equipment_vendor"] = doc_vendor

            # Create merged document
            merged_meta = base_meta.copy()
            merged_meta.update(doc_metadata)
            merged_meta["file_name"] = file_name
            from llama_index.core.schema import Document
            merged_doc = Document(text=full_text, metadata=merged_meta)

            doc_nodes = self.pdf_chunker.get_nodes_from_documents([merged_doc])
            
            for node in doc_nodes:
                # Ensure every section chunk inherits document-level metadata
                for k, v in doc_metadata.items():
                    if k not in node.metadata or not node.metadata[k]:
                        node.metadata[k] = v
                
                if "file_name" not in node.metadata:
                    node.metadata["file_name"] = file_name
                    
                # Explicitly prepend the file name to the chunk text so BM25 and Vector search always have context
                if not node.text.startswith("[Context:"):
                    node.text = f"[Context: {node.metadata['file_name']}]\n" + node.text
            
            nodes.extend(doc_nodes)

        logger.info(f"Produced and enriched {len(nodes)} structural chunks.")

        logger.info("Data pipeline finished.")
        return nodes
