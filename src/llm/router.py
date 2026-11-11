import json
import os
import logging
import re

logger = logging.getLogger("netrestore")

class SemanticRouter:
    """Route telecom queries via node ID patterns, syslog signatures, and keywords."""

    # Node IDs always follow the pattern: LOCATION-ROLE-NN (e.g., BAS-ACC-05, BLR-CORE-01)
    _NODE_ID_RE = re.compile(r'\b[A-Z]{2,5}-(?:CORE|PE|ACC|AGG|CE|P|RR)-\d{2}\b', re.IGNORECASE)
    def __init__(self, config_path: str = None):
        if not config_path:
            config_path = os.path.abspath(
                os.path.join(os.path.dirname(__file__), "..", "..", "config", "keywords.json")
            )
        self.keywords = self._load_keywords(config_path)

    def _load_keywords(self, config_path: str) -> list[str]:
        if os.path.exists(config_path):
            with open(config_path, "r") as f:
                data = json.load(f)
                return data.get("telecom_keywords", [])
        logger.warning("Warning: keywords.json was not found. The router has no configured keywords.")
        return []

    def is_node_reference(self, text: str) -> bool:
        """Return True if the text mentions a topology node ID (e.g. BAS-ACC-05)."""
        return bool(self._NODE_ID_RE.search(text))

    def is_alarm_reference(self, text: str) -> bool:
        """Return True if the text mentions an alarm code or alarm reference."""
        return bool(re.search(r'\bALARM(?:[_\s-]*(?:CODE)?[_\s-]*)?\d+\b|\bALARM\b', text, re.IGNORECASE))

    def is_syslog(self, text: str) -> bool:
        """Detect if the input looks like a raw syslog or telemetry dump."""
        syslog_patterns = [
            r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b',  # IP Address
            r'%[A-Z0-9_]+-\d-[A-Z0-9_]+',          # Syslog tag e.g., %SYS-5-CONFIG
            r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2}\s+\d{2}:\d{2}:\d{2}', # Timestamp
            r'\bALARM(?:[_\s-]*(?:CODE)?[_\s-]*)?\d+\b'  # Custom mock alarm codes (ALARM_3049, ALARM 3049, etc.)
        ]
        for pattern in syslog_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False
        
    def extract_ip(self, text: str) -> str:
        """Extract the first IPv4 address found in the text for Graph Retrieval."""
        match = re.search(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b', text)
        if match:
            return match.group(0)
        return ""

    def classify(self, query: str, has_memory: bool = False) -> str:
        """Return ``telecom`` for supported queries/syslogs and ``general`` otherwise."""
        # 1. Follow-up messages in an active session are always in scope.
        if has_memory:
            return "telecom"

        # 2. Any mention of a topology node ID is unambiguously telecom.
        if self.is_node_reference(query):
            logger.debug("Router: node ID pattern detected — classified as telecom.")
            return "telecom"

        # 3. Any mention of an alarm code (e.g. ALARM 3049, ALARM_3049).
        if self.is_alarm_reference(query):
            return "telecom"

        # 4. Raw syslog / telemetry dumps (IP, timestamp, alarm codes).
        if self.is_syslog(query):
            return "telecom"

        # 5. Standalone 3-5 digit number (e.g. '3049').
        if query.strip().isdigit() and 3 <= len(query.strip()) <= 5:
            return "telecom"

        # 6. Keyword match against the configured vocabulary with word boundaries
        # Prevents false positive substring matches (e.g., 'airport' matching 'port')
        query_lower = query.lower()
        query_words = set(re.findall(r'\b[a-z0-9_-]+\b', query_lower))
        for keyword in self.keywords:
            kw = keyword.lower()
            if " " in kw or "-" in kw:
                if kw in query_lower:
                    return "telecom"
            else:
                if kw in query_words:
                    return "telecom"

        return "general"

