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
        
    def load_documents(self) -> list[Document]:
        """Load approved SOP PDFs from the configured corpus directory."""
        if not os.path.exists(self.data_dir):
            logger.warning(f"Directory {self.data_dir} not found.")
            return []
            
        logger.info(f"Loading documents from {self.data_dir}.")
        
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
            input_dir=self.data_dir,
            recursive=True,
            required_exts=self.required_exts,
            file_extractor=file_extractor if file_extractor else None
        )
        documents = reader.load_data()
        logger.info(f"Successfully loaded {len(documents)} document pages/files.")
        return documents
