"""Hybrid retrieval using dense search, BM25, RRF, reranking, and Graph Context."""

import os
import pickle
import json
import logging

from llama_index.core.retrievers import BaseRetriever, VectorIndexRetriever
from llama_index.core.vector_stores import MetadataFilters, ExactMatchFilter
from llama_index.core.schema import NodeWithScore, QueryBundle
from collections import defaultdict

from src.retrieval.reranker import TelecomReranker
from src.retrieval.tokenizer import telecom_tokenize

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
        # Build an inverted file-to-nodes map for O(1) SOP context expansion
        self.file_to_nodes = defaultdict(list)
        for node in self.nodes:
            fn = node.metadata.get("file_name") if hasattr(node, "metadata") else None
            if fn:
                self.file_to_nodes[fn].append(node)

    def _retrieve(self, query_bundle: QueryBundle, filters: dict = None) -> list[NodeWithScore]:
        if not self.bm25:
            return []
            
        # Use centralized telecom tokenizer (DRY) to ensure indexing and querying stay in sync
        query = telecom_tokenize(query_bundle.query_str)
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
        
        candidates = fused
        if self.reranker and len(fused) > 0:
            try:
                candidates = self.reranker.rerank(query, fused, top_n=self.similarity_top_k)
            except Exception as e:
                logger.warning(f"Reranking failed, skipping reranker: {e}")
                candidates = fused[:self.similarity_top_k]
        else:
            candidates = fused[:self.similarity_top_k]

        # SOP Context Expansion: Guarantee that critical procedural sections
        # (Resolution Steps, Diagnostic Commands, Post-Check) for the top matching SOP are included.
        if candidates and hasattr(self, 'sparse_retriever') and self.sparse_retriever and self.sparse_retriever.nodes:
            top_file = candidates[0].node.metadata.get("file_name")
            if top_file:
                existing_headers = {c.node.metadata.get("header_path") for c in candidates if c.node.metadata.get("file_name") == top_file}
                needed_sections = [
                    "Diagnostic Commands & Expected Outputs",
                    "Resolution Steps",
                    "Post-Check Verification"
                ]
                additional_nodes = []
                # Fast lookup via inverted file-to-nodes index with fallback
                file_nodes = getattr(self.sparse_retriever, 'file_to_nodes', {}).get(top_file, [])
                if not file_nodes and self.sparse_retriever.nodes:
                    file_nodes = [n for n in self.sparse_retriever.nodes if n.metadata.get("file_name") == top_file]

                for node in file_nodes:
                    h = node.metadata.get("header_path")
                    if h in needed_sections and h not in existing_headers:
                        additional_nodes.append(NodeWithScore(node=node, score=candidates[0].score))
                        existing_headers.add(h)
                if additional_nodes:
                    candidates = additional_nodes + candidates

        return candidates[:self.similarity_top_k]

    def get_retriever(self, filters: dict = None) -> BaseRetriever:
        """Returns a LlamaIndex-compatible BaseRetriever wrapper with baked-in filters."""
        hybrid_parent = self
        
        class WrapperRetriever(BaseRetriever):
            def __init__(self):
                super().__init__()
                
            def _retrieve(self, query_bundle: QueryBundle, **kwargs) -> list[NodeWithScore]:
                return hybrid_parent.search(query_bundle.query_str, filters)
                
        return WrapperRetriever()



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
    if not os.path.exists(bm25_path):
        alt_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "shared_data", "bm25_index.pkl"))
        if os.path.exists(alt_path):
            bm25_path = alt_path
    last_modified = os.path.getmtime(bm25_path) if os.path.exists(bm25_path) else 0.0
    bm25_data = load_bm25_cache(bm25_path, last_modified)
    
    retriever = TelecomHybridRetriever()
    retriever.vector_retriever = VectorRetriever(vs_manager)
    retriever.sparse_retriever = SparseRetriever(bm25_data)
    retriever.reranker = TelecomReranker()
    return retriever
