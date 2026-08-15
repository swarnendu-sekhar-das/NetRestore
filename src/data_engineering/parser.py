import os
from llama_index.core import SimpleDirectoryReader
from llama_index.core.schema import Document
import logging

logger = logging.getLogger("netrestore")


# The production corpus currently contains SOP PDFs only.
# This prevents configuration and evaluation JSON from being indexed.
SOP_FILE_EXTENSIONS = [".pdf"]

class TelecomDocumentParser:
    """Load approved SOP PDFs for the chunking pipeline."""
    
    def __init__(self, data_dir: str, required_exts: list[str] | None = None):
        self.data_dir = data_dir
        self.required_exts = required_exts or SOP_FILE_EXTENSIONS
        
    def load_documents(self, processed_files: set = None) -> list[Document]:
        """Load approved SOP PDFs, skipping those already processed."""
        if not os.path.exists(self.data_dir):
            logger.warning(f"Directory {self.data_dir} not found.")
            return []
            
        if processed_files is None:
            processed_files = set()
            
        # List all valid files in the data directory
        all_files = []
        for root, _, files in os.walk(self.data_dir):
            for file in files:
                if any(file.endswith(ext) for ext in self.required_exts):
                    all_files.append(os.path.join(root, file))
                    
        # Filter out already processed files
        files_to_process = [f for f in all_files if os.path.basename(f) not in processed_files]
        
        if not files_to_process:
            logger.info("No new documents to parse.")
            return []
            
        logger.info(f"Found {len(files_to_process)} new documents to load (skipped {len(all_files) - len(files_to_process)}).")
        
        # Use LlamaParse when it is configured; otherwise use the default PDF reader.
        file_extractor = {}
        llama_api_key = os.environ.get("LLAMA_CLOUD_API_KEY")
        if llama_api_key:
            try:
                from llama_parse import LlamaParse
                logger.info("LlamaParse API Key found. Using LlamaParse for complex PDFs.")
                file_extractor[".pdf"] = LlamaParse(result_type="markdown")
            except ImportError:
                logger.warning("llama_parse not installed. Falling back to default PyPDF.")
        else:
            logger.info("No LLAMA_CLOUD_API_KEY found. Using standard PyPDF for PDF parsing.")

        reader = SimpleDirectoryReader(
            input_files=files_to_process,
            file_extractor=file_extractor if file_extractor else None
        )
        documents = reader.load_data()
        logger.info(f"Successfully loaded {len(documents)} document pages/files.")
        return documents
