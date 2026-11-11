"""Telecom-specific tokenizer for BM25 sparse search and data ingestion."""

import re

# Standard English stopwords to filter out from general text
STOPWORDS = {
    'the', 'a', 'an', 'in', 'on', 'at', 'of', 'for', 'to', 'and', 'or', 'is', 'are',
    'was', 'were', 'it', 'with', 'as', 'by', 'from', 'that', 'this', 'these', 'those',
    'then', 'so', 'can', 'will', 'be', 'has', 'have', 'had', 'do', 'does', 'did', 'but',
    'not', 'what', 'which', 'who', 'how', 'when', 'where', 'why'
}

# Pre-compiled regex patterns for efficient token extraction
NODE_ID_RE = re.compile(r'\b[A-Za-z]+-[A-Za-z]+-\d+\b')
ALARM_CODE_RE = re.compile(r'\bALARM(?:[_\s-]*(?:CODE)?[_\s-]*)?(\d+)\b')
DIGITS_RE = re.compile(r'\b\d{3,5}\b')
WORDS_RE = re.compile(r'[a-zA-Z]{2,}')


def telecom_tokenize(text: str) -> list[str]:
    """
    Extract Telecom Node IDs, Alarm Codes, digits, and domain words for sparse retrieval.
    Used consistently across both BM25 index creation and runtime hybrid querying.
    """
    text_upper = text.upper()
    tokens = []

    # 1. Extract Node IDs: LOCATION-ROLE-NN (e.g., BAS-ACC-05, IND-ACC-16)
    node_ids = NODE_ID_RE.findall(text_upper)
    tokens.extend([nid.lower() for nid in node_ids])

    # 2. Extract Alarm Codes with any separator (e.g., ALARM_3049, ALARM 3049, ALARM-3049, ALARM CODE 3049)
    alarm_codes = ALARM_CODE_RE.findall(text_upper)
    for code in alarm_codes:
        tokens.append(f"alarm_{code}")
        tokens.append(code)

    # 3. Standalone 3-5 digit alarm numbers (e.g., '3049')
    digits = DIGITS_RE.findall(text_upper)
    for d in digits:
        tokens.append(f"alarm_{d}")
        tokens.append(d)

    # 4. Domain keywords and natural language words
    words = WORDS_RE.findall(text.lower())
    tokens.extend([w for w in words if w not in STOPWORDS])

    return tokens
