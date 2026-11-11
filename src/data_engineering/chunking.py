import os
import re
from typing import List, Dict, Any, Optional

from llama_index.core.schema import TextNode, BaseNode
from llama_index.core.node_parser import MarkdownNodeParser
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

        # Match alarm codes such as ALARM_CODE_404, ALARM_501, ALARM 3049, etc.
        alarm_match = re.search(r'\bALARM(?:[_\s-]*(?:CODE)?[_\s-]*)?(\d+)\b', text, re.IGNORECASE)
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


class RegexSOPParser:
    """Custom Node Parser to chunk SOP PDFs using structural anchor words."""
    
    def __init__(self):
        self.sections = [
            "Description",
            "Pre-requisite Checks",
            "Potential Root Causes",
            "Diagnostic Commands & Expected Outputs",
            "Resolution Steps",
            "Post-Check Verification",
            "Roll-back Procedures"
        ]
        
    def get_nodes_from_documents(self, documents: List[Any], **kwargs) -> List[BaseNode]:
        nodes = []
        for doc in documents:
            text = doc.get_content()
            
            # Split the text by section headers using Regex with line boundaries to avoid splitting on inline field labels.
            pattern = r'(?:\n|^)\s*(' + '|'.join(self.sections) + r')\s*\n'
            parts = re.split(pattern, text)
            
            # First part is the document title and metadata
            sections_dict = {"Header": parts[0]}
            
            # Iterate through the rest of the parts
            for i in range(1, len(parts), 2):
                if i+1 < len(parts):
                    sec_title = parts[i].strip()
                    sec_content = parts[i+1].strip()
                    sections_dict[sec_title] = sec_content
                    
            # Create a node for each structural section
            for title, content in sections_dict.items():
                if content.strip():
                    meta = doc.metadata.copy() if hasattr(doc, 'metadata') and doc.metadata else {}
                    meta["header_path"] = title
                    node = TextNode(
                        text=f"[{title}]\n{content.strip()}",
                        metadata=meta
                    )
                    nodes.append(node)
                    
        return nodes


def get_pdf_chunker():
    """Return a regex-based structural parser for SOP PDFs."""
    return RegexSOPParser()
