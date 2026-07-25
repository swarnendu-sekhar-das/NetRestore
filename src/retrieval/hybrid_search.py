"""Hybrid retrieval using dense search, BM25, RRF, and reranking."""

from llama_index.core.retrievers import BaseRetriever, VectorIndexRetriever
from llama_index.core.vector_stores import MetadataFilters, ExactMatchFilter
from llama_index.core.schema import NodeWithScore, TextNode, QueryBundle
from rank_bm25 import BM25Okapi
import logging

from src.retrieval.reranker import TelecomReranker

logger = logging.getLogger("netrestore")


class TelecomHybridRetriever:
    """Create the dense, BM25, and reranking parts of the retriever."""

    def __init__(self, vector_store_manager, similarity_top_k: int = 10):
        self.vs_manager = vector_store_manager
        self.index = vector_store_manager.get_index()
        self.similarity_top_k = similarity_top_k

        # Build a local BM25 index from the stored documents.
        self._build_bm25_index()

        # Load the cross-encoder used for final ranking.
        self.reranker = TelecomReranker()

    def _build_bm25_index(self):
        """Build the in-memory BM25 index from the ChromaDB collection."""
        collection = self.vs_manager.chroma_collection
        results = collection.get(include=["documents", "metadatas"])

        self.bm25_corpus_ids = results["ids"]
        self.bm25_corpus_docs = results["documents"]
        self.bm25_corpus_metas = results["metadatas"]

        if not self.bm25_corpus_docs:
            logger.warning("Warning: ChromaDB collection is empty. BM25 index was not built.")
            self.bm25 = None
            return

        tokenized = [doc.lower().split() for doc in self.bm25_corpus_docs]
        self.bm25 = BM25Okapi(tokenized)
        logger.info(f"BM25 index built for {len(self.bm25_corpus_docs)} documents.")

    def get_retriever(self, filters: dict = None):
        """Return a fusion retriever configured with optional metadata filters."""
        # Convert the dictionary into LlamaIndex metadata filters.
        llama_filters = None
        if filters:
            filter_params = [
                ExactMatchFilter(key=k, value=v)
                for k, v in filters.items()
            ]
            llama_filters = MetadataFilters(filters=filter_params)

        # Use the same filters for the dense retriever.
        vector_retriever = VectorIndexRetriever(
            index=self.index,
            similarity_top_k=self.similarity_top_k,
            filters=llama_filters,
        )

        return TelecomFusionRetriever(
            vector_retriever=vector_retriever,
            bm25=self.bm25,
            bm25_corpus_ids=self.bm25_corpus_ids,
            bm25_corpus_docs=self.bm25_corpus_docs,
            bm25_corpus_metas=self.bm25_corpus_metas,
            reranker=self.reranker,
            filters=filters,
            similarity_top_k=self.similarity_top_k,
            rerank_top_n=3,
        )

    def search(self, query: str, filters: dict = None):
        """Convenience method to retrieve nodes for a given query and filters."""
        retriever = self.get_retriever(filters)
        return retriever.retrieve(query)


class TelecomFusionRetriever(BaseRetriever):
    """Fuse dense and BM25 results, then rerank the candidates."""

    def __init__(
        self,
        vector_retriever,
        bm25,
        bm25_corpus_ids,
        bm25_corpus_docs,
        bm25_corpus_metas,
        reranker,
        filters=None,
        similarity_top_k=10,
        rerank_top_n=3,
    ):
        super().__init__()
        self._vector_retriever = vector_retriever
        self._bm25 = bm25
        self._bm25_corpus_ids = bm25_corpus_ids
        self._bm25_corpus_docs = bm25_corpus_docs
        self._bm25_corpus_metas = bm25_corpus_metas
        self._reranker = reranker
        self._filters = filters
        self._similarity_top_k = similarity_top_k
        self._rerank_top_n = rerank_top_n

    def _retrieve(self, query_bundle: QueryBundle) -> list[NodeWithScore]:
        """Retrieve dense and BM25 candidates, fuse them, and rerank them."""
        query = query_bundle.query_str

        # Retrieve semantic matches from the vector index.
        vector_results = self._vector_retriever.retrieve(query)

        # Retrieve keyword matches from the BM25 index.
        if self._bm25 is not None:
            bm25_results = self._bm25_search(query, top_k=self._similarity_top_k)
        else:
            bm25_results = []

        # Combine the two ranked result lists.
        if bm25_results:
            fused = self._reciprocal_rank_fusion(vector_results, bm25_results)
        else:
            fused = vector_results

        # Use the cross-encoder to rank the remaining candidates.
        if self._reranker and len(fused) > 0:
            return self._reranker.rerank(query, fused, top_n=self._rerank_top_n)

        return fused[: self._rerank_top_n]

    # BM25 search with metadata filtering.

    def _bm25_search(self, query: str, top_k: int = 10) -> list[NodeWithScore]:
        """
        Score all documents with BM25, apply metadata filters, return top-k.
        """
        tokenized_query = query.lower().split()
        scores = self._bm25.get_scores(tokenized_query)

        # Keep positive scores that match the active metadata filters.
        candidates = []
        for idx, score in enumerate(scores):
            if score <= 0:
                continue
            meta = self._bm25_corpus_metas[idx] if self._bm25_corpus_metas else {}
            if self._matches_filters(meta):
                candidates.append((idx, score))

        # Sort by score and keep the requested number of results.
        candidates.sort(key=lambda x: x[1], reverse=True)
        top_candidates = candidates[:top_k]

        # Convert BM25 results back into LlamaIndex nodes.
        results = []
        for idx, score in top_candidates:
            node = TextNode(
                text=self._bm25_corpus_docs[idx],
                id_=self._bm25_corpus_ids[idx],
                metadata=self._bm25_corpus_metas[idx] if self._bm25_corpus_metas else {},
            )
            results.append(NodeWithScore(node=node, score=float(score)))

        return results

    def _matches_filters(self, metadata: dict) -> bool:
        """Check if a document's metadata passes all active filters."""
        if not self._filters:
            return True
        for key, value in self._filters.items():
            if metadata.get(key) != value:
                return False
        return True

    # Reciprocal Rank Fusion.

    @staticmethod
    def _reciprocal_rank_fusion(
        vector_results: list[NodeWithScore],
        bm25_results: list[NodeWithScore],
        k: int = 60,
    ) -> list[NodeWithScore]:
        """
        Merge results from two retrievers using Reciprocal Rank Fusion (RRF).

        RRF formula:  score(d) = Σ  1 / (k + rank_i(d))
        where rank_i is the rank from retriever i.  k=60 is the standard
        smoothing constant from the original RRF paper (Cormack et al., 2009).

        Documents appearing in both result lists get a combined (higher) score.
        """
        fused_scores: dict[str, float] = {}
        node_map: dict[str, NodeWithScore] = {}

        for rank, result in enumerate(vector_results):
            node_id = result.node.node_id
            fused_scores[node_id] = fused_scores.get(node_id, 0.0) + 1.0 / (k + rank + 1)
            node_map[node_id] = result

        for rank, result in enumerate(bm25_results):
            node_id = result.node.node_id
            fused_scores[node_id] = fused_scores.get(node_id, 0.0) + 1.0 / (k + rank + 1)
            if node_id not in node_map:
                node_map[node_id] = result

        # Return results in descending fused-score order.
        sorted_ids = sorted(fused_scores.keys(), key=lambda nid: fused_scores[nid], reverse=True)

        fused = []
        for node_id in sorted_ids:
            result = node_map[node_id]
            result.score = fused_scores[node_id]
            fused.append(result)

        return fused
