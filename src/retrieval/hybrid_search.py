"""Hybrid retrieval using dense search, BM25, RRF, reranking, and Graph Context."""

import os
import pickle
import json
import logging
import streamlit as st
from llama_index.core.retrievers import BaseRetriever, VectorIndexRetriever
from llama_index.core.vector_stores import MetadataFilters, ExactMatchFilter
from llama_index.core.schema import NodeWithScore, QueryBundle

from src.retrieval.reranker import TelecomReranker

logger = logging.getLogger("netrestore")

class VectorRetriever(BaseRetriever):
    """Dense semantic search retriever (SRP applied)."""
    def __init__(self, vector_store_manager, similarity_top_k=10):
        super().__init__()
        self.index = vector_store_manager.get_index()
        self.similarity_top_k = similarity_top_k

    def _retrieve(self, query_bundle: QueryBundle, filters: dict = None) -> list[NodeWithScore]:
        llama_filters = None
        if filters:
            filter_params = [ExactMatchFilter(key=k, value=v) for k, v in filters.items()]
            llama_filters = MetadataFilters(filters=filter_params)
            
        retriever = VectorIndexRetriever(
            index=self.index,
            similarity_top_k=self.similarity_top_k,
            filters=llama_filters,
        )
        return retriever.retrieve(query_bundle.query_str)


class SparseRetriever(BaseRetriever):
    """BM25 keyword search retriever (SRP applied)."""
    def __init__(self, bm25_data, similarity_top_k=10):
        super().__init__()
        self.bm25 = bm25_data.get("bm25")
        self.nodes = bm25_data.get("nodes", [])
        self.similarity_top_k = similarity_top_k

    def _retrieve(self, query_bundle: QueryBundle, filters: dict = None) -> list[NodeWithScore]:
        if not self.bm25:
            return []
            
        import re
        def tokenize(text):
            # Extract only Telecom Node IDs and Alarm Codes for sparse retrieval to prevent syslog noise dilution
            special_tokens = re.findall(r'[A-Za-z]+-[A-Za-z]+-\d+|ALARM_\d+', text.upper())
            if special_tokens:
                return [t.lower() for t in special_tokens]
            return re.findall(r'[\w-]+', text.lower())
            
        query = tokenize(query_bundle.query_str)
        scores = self.bm25.get_scores(query)
        
        candidates = []
        for idx, score in enumerate(scores):
            if score <= 0:
                continue
            meta = self.nodes[idx].metadata if hasattr(self.nodes[idx], 'metadata') else {}
            if self._matches_filters(meta, filters):
                candidates.append((idx, score))
                
        candidates.sort(key=lambda x: x[1], reverse=True)
        top_candidates = candidates[:self.similarity_top_k]
        
        results = []
        for idx, score in top_candidates:
            node = self.nodes[idx]
            results.append(NodeWithScore(node=node, score=float(score)))
            
        return results

    def _matches_filters(self, metadata: dict, filters: dict) -> bool:
        if not filters:
            return True
        for key, value in filters.items():
            if metadata.get(key) != value:
                return False
        return True


class RRFCombiner:
    """Merges results from multiple retrievers using Reciprocal Rank Fusion."""
    @staticmethod
    def fuse(results_list: list[list[NodeWithScore]], k: int = 60, top_n: int = 10) -> list[NodeWithScore]:
        fused_scores = {}
        node_map = {}
        
        for results in results_list:
            for rank, result in enumerate(results):
                node_id = result.node.node_id
                fused_scores[node_id] = fused_scores.get(node_id, 0.0) + 1.0 / (k + rank + 1)
                node_map[node_id] = result
                
        sorted_ids = sorted(fused_scores.keys(), key=lambda nid: fused_scores[nid], reverse=True)
        
        fused = []
        for node_id in sorted_ids[:top_n]:
            result = node_map[node_id]
            result.score = fused_scores[node_id]
            fused.append(result)
            
        return fused


class GraphRetriever:
    """Queries network_topology.json for Blast Radius context."""
    def __init__(self, topology_path="data/network_topology.json"):
        self.topology_path = topology_path
        self.nodes = []
        self._load_topology()
        
    def _load_topology(self):
        if not os.path.exists(self.topology_path):
            logger.warning(f"Topology file not found at {self.topology_path}")
            return
        with open(self.topology_path, 'r') as f:
            data = json.load(f)
            self.nodes = data.get("nodes", [])
            
    def get_blast_radius(self, ip_address: str) -> str:
        if not ip_address:
            return ""
        for node in self.nodes:
            if node.get("ip_address") == ip_address:
                neighbors = [n.get("node_id") for n in node.get("neighbors", [])]
                if neighbors:
                    return f"BLAST RADIUS WARNING: Node {node.get('node_id')} ({ip_address}) is connected to {', '.join(neighbors)}."
                return f"Node {node.get('node_id')} ({ip_address}) has no critical downstream neighbors."
        return ""


class TelecomHybridRetriever:
    """Facade for the UI to call the fused retrieval easily."""
    def __init__(self, vector_store_manager=None, similarity_top_k=10, bm25_path="shared_data/bm25_index.pkl"):
        # For backward compatibility with existing evaluate/test scripts
        if vector_store_manager:
            last_modified = os.path.getmtime(bm25_path) if os.path.exists(bm25_path) else 0.0
            bm25_data = load_bm25_cache(bm25_path, last_modified)
            self.vector_retriever = VectorRetriever(vector_store_manager, similarity_top_k)
            self.sparse_retriever = SparseRetriever(bm25_data, similarity_top_k)
            self.reranker = TelecomReranker()
        self.similarity_top_k = similarity_top_k

    def search(self, query: str, filters: dict = None):
        bundle = QueryBundle(query_str=query)
        
        v_results = []
        try:
            v_results = self.vector_retriever._retrieve(bundle, filters)
        except Exception as e:
            logger.warning(f"Vector retrieval failed, falling back to BM25-only: {e}")

        s_results = []
        try:
            s_results = self.sparse_retriever._retrieve(bundle, filters)
        except Exception as e:
            logger.warning(f"Sparse retrieval failed, falling back to dense-only: {e}")
            
        if not v_results and not s_results:
            logger.error("Both retrievers failed. Returning empty results.")
            return []
            
        fused = RRFCombiner.fuse([r for r in [v_results, s_results] if r], top_n=self.similarity_top_k)
        
        if self.reranker and len(fused) > 0:
            try:
                return self.reranker.rerank(query, fused, top_n=self.similarity_top_k)
            except Exception as e:
                logger.warning(f"Reranking failed, skipping reranker: {e}")
                return fused[:self.similarity_top_k]
                
        return fused[:self.similarity_top_k]

    def get_retriever(self, filters: dict = None) -> BaseRetriever:
        """Returns a LlamaIndex-compatible BaseRetriever wrapper with baked-in filters."""
        hybrid_parent = self
        
        class WrapperRetriever(BaseRetriever):
            def __init__(self):
                super().__init__()
                
            def _retrieve(self, query_bundle: QueryBundle, **kwargs) -> list[NodeWithScore]:
                return hybrid_parent.search(query_bundle.query_str, filters)
                
        return WrapperRetriever()


@st.cache_resource
def load_bm25_cache(file_path: str, _last_modified: float):
    """
    Global Singleton Cache for BM25.
    Streamlit ignores parameters starting with _ for hashing, but uses them for invalidation.
    """
    logger.info("Loading BM25 matrix into global Streamlit cache...")
    if not os.path.exists(file_path):
        logger.warning(f"BM25 index not found at {file_path}")
        return {}
    with open(file_path, 'rb') as f:
        return pickle.load(f)

def get_hybrid_retriever(vs_manager, bm25_path="shared_data/bm25_index.pkl"):
    """Dependency Injection factory for Streamlit UI."""
    last_modified = os.path.getmtime(bm25_path) if os.path.exists(bm25_path) else 0.0
    bm25_data = load_bm25_cache(bm25_path, last_modified)
    
    retriever = TelecomHybridRetriever()
    retriever.vector_retriever = VectorRetriever(vs_manager)
    retriever.sparse_retriever = SparseRetriever(bm25_data)
    retriever.reranker = TelecomReranker()
    return retriever
