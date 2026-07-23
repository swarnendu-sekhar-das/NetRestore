import os
import re
from typing import List, Dict, Any, Optional

from llama_index.core.schema import TextNode, BaseNode
from llama_index.core.node_parser import MarkdownNodeParser, SentenceSplitter
from llama_index.core.extractors import BaseExtractor


class TelecomMetadataExtractor(BaseExtractor):
    """
    Custom metadata extractor that uses Regex to identify Alarm Codes
    and Equipment Vendors from the document text.
    In a real-world scenario, this might use an LLM for complex extraction.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    async def aextract(self, nodes: List[BaseNode]) -> List[Dict[str, Any]]:
        """Extract metadata from nodes."""
        metadata_list = []
        for node in nodes:
            metadata = self._extract_metadata(node.get_content())
            metadata_list.append(metadata)
        return metadata_list

    def _extract_metadata(self, text: str) -> Dict[str, Any]:
        """Apply regex patterns to find specific telecom entities."""
        metadata = {}

        # Extract Alarm Code (e.g. ALARM_CODE_404, ALARM_501)
        alarm_match = re.search(r'ALARM(?:_CODE)?_(\d+)', text, re.IGNORECASE)
        if alarm_match:
            metadata["alarm_code"] = alarm_match.group(1)

        # Extract Vendor (expanded to include Arista)
        vendors = ["Cisco", "Nokia", "Juniper", "Ericsson", "Huawei", "Arista"]
        for vendor in vendors:
            if vendor.lower() in text.lower():
                metadata["equipment_vendor"] = vendor
                break

        # If no vendor found in chunk, we don't set it (pipeline will propagate)

        # Extract Severity
        severity_match = re.search(r'Severity:\s*(Critical|Major|Minor|Warning)', text, re.IGNORECASE)
        if severity_match:
            metadata["severity"] = severity_match.group(1).title()

        # Extract Node ID
        node_match = re.search(r'NodeID:\s*([\w-]+)', text, re.IGNORECASE)
        if node_match:
            metadata["node_id"] = node_match.group(1)

        return metadata


def get_markdown_chunker():
    """
    Returns a MarkdownNodeParser for .md documents.
    Chunks text by Header (e.g. ## Procedure X), guaranteeing
    that all steps under a procedure stay in the same node.
    """
    return MarkdownNodeParser()


def get_pdf_chunker():
    """
    Returns a SentenceSplitter for .pdf documents.
    PDF text loaded via PyPDF comes out as flat, unstructured plain text
    with no Markdown headers. MarkdownNodeParser would produce a single
    giant blob on PDF content — SentenceSplitter handles it correctly
    by splitting on sentence boundaries with a fixed token budget.
    """
    return SentenceSplitter(chunk_size=512, chunk_overlap=64)
