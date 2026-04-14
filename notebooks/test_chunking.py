"""
CI Unit Tests: Data Pipeline Chunking
Verifies DataPipeline loads and chunks SOP documents correctly.
Jenkins runs this in the 'Lint & Unit Test' stage via:
  python -m pytest notebooks/test_chunking.py -v
"""
import os
import sys
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.data_engineering.pipeline import DataPipeline

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))


def test_all_vendor_files_present():
    """All 5 vendor SOP files must exist in ./data/"""
    expected = [
        "cisco_ios_xr_sop.md",
        "nokia_router_mop.md",
        "ericsson_ipos_sop.md",
        "juniper_junos_sop.md",
        "huawei_vrp_sop.md",
    ]
    for fname in expected:
        assert os.path.exists(os.path.join(DATA_DIR, fname)), f"Missing: {fname}"


def test_pipeline_loads_documents():
    """DataPipeline must load at least 100 documents."""
    pipeline = DataPipeline(data_dir=DATA_DIR)
    docs = pipeline.load_documents()
    assert len(docs) >= 100, f"Expected >=100 docs, got {len(docs)}"


def test_pipeline_produces_chunks():
    """DataPipeline must produce at least 100 chunks after processing."""
    pipeline = DataPipeline(data_dir=DATA_DIR)
    docs = pipeline.load_documents()
    nodes = pipeline.chunk_documents(docs)
    assert len(nodes) >= 100, f"Expected >=100 chunks, got {len(nodes)}"


def test_chunk_metadata_has_vendor():
    """Every chunk must carry equipment_vendor metadata for hybrid filtering."""
    pipeline = DataPipeline(data_dir=DATA_DIR)
    docs = pipeline.load_documents()
    nodes = pipeline.chunk_documents(docs)
    vendors = {n.metadata.get("equipment_vendor") for n in nodes}
    assert len(vendors - {None}) >= 5, f"Expected 5 vendors, found: {vendors}"


if __name__ == "__main__":
    # Also runnable as plain script (for manual inspection)
    pipeline = DataPipeline(data_dir=DATA_DIR)
    docs = pipeline.load_documents()
    nodes = pipeline.chunk_documents(docs)
    print(f"Loaded {len(docs)} docs → {len(nodes)} chunks")
    for node in nodes[:3]:
        print(node.metadata, node.get_content()[:100])
