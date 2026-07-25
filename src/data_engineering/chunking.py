import os
import re
from typing import List, Dict, Any, Optional

from llama_index.core.schema import TextNode, BaseNode
from llama_index.core.node_parser import MarkdownNodeParser, SentenceSplitter
from llama_index.core.extractors import BaseExtractor


class TelecomMetadataExtractor(BaseExtractor):
    """Extract basic telecom metadata from a chunk with regular expressions."""

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

        # Match alarm codes such as ALARM_CODE_404 and ALARM_501.
        alarm_match = re.search(r'ALARM(?:_CODE)?_(\d+)', text, re.IGNORECASE)
        if alarm_match:
            metadata["alarm_code"] = alarm_match.group(1)

        # Match a supported equipment vendor.
        vendors = ["Cisco", "Nokia", "Juniper", "Ericsson", "Huawei", "Arista"]
        for vendor in vendors:
            if vendor.lower() in text.lower():
                metadata["equipment_vendor"] = vendor
                break

        # The pipeline can add the document vendor when this is missing.

        # Match the alarm severity.
        severity_match = re.search(r'Severity:\s*(Critical|Major|Minor|Warning)', text, re.IGNORECASE)
        if severity_match:
            metadata["severity"] = severity_match.group(1).title()

        # Match the node ID.
        node_match = re.search(r'NodeID:\s*([\w-]+)', text, re.IGNORECASE)
        if node_match:
            metadata["node_id"] = node_match.group(1)

        return metadata


def get_markdown_chunker():
    """Return a header-based chunker for Markdown documents."""
    return MarkdownNodeParser()


def get_pdf_chunker():
    """Return a sentence-based chunker for text extracted from PDFs."""
    return SentenceSplitter(chunk_size=512, chunk_overlap=64)
