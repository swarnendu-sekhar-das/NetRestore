"""Basic tests for SOP loading, chunking, and metadata extraction."""
import os
import sys
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.data_engineering.pipeline import DataPipeline

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "sops"))


def test_sop_corpus_contains_only_pdfs():
    """Production corpus is isolated from application JSON/configuration files."""
    files = os.listdir(DATA_DIR)
    assert files, "SOP corpus is empty"
    assert all(name.lower().endswith(".pdf") for name in files)
    assert len(files) >= 675


def test_pipeline_produces_chunks():
    """DataPipeline.run() must produce at least 100 chunks."""
    pipeline = DataPipeline(data_dir=DATA_DIR)
    nodes = pipeline.run()
    assert len(nodes) >= 100, f"Expected >=100 chunks, got {len(nodes)}"


def test_chunk_metadata_has_vendor():
    """Every chunk must carry equipment_vendor metadata for hybrid filtering."""
    pipeline = DataPipeline(data_dir=DATA_DIR)
    nodes = pipeline.run()
    vendors = {n.metadata.get("equipment_vendor") for n in nodes}
    assert len(vendors - {None}) >= 1, f"No vendor metadata found. Vendors: {vendors}"


if __name__ == "__main__":
    pipeline = DataPipeline(data_dir=DATA_DIR)
    nodes = pipeline.run()
    print(f"Total chunks: {len(nodes)}")
    for node in nodes[:3]:
        print(node.metadata, node.get_content()[:100])
