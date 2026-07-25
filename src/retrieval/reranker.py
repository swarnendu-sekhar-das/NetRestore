"""Cross-encoder reranking for candidates returned by hybrid retrieval."""

from llama_index.core.schema import NodeWithScore
import logging

logger = logging.getLogger("netrestore")


class TelecomReranker:
    """Wrap a CrossEncoder and fall back to retrieval scores if it is unavailable."""

    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):
        try:
            from sentence_transformers import CrossEncoder
            self.model = CrossEncoder(model_name)
            self.available = True
            logger.info(f"Reranker loaded: {model_name}")
        except ImportError as e:
            logger.warning(f"Warning: Reranker model could not be loaded: {e}. Using retrieval scores instead.")
            self.model = None
            self.available = False

    def rerank(
        self,
        query: str,
        nodes_with_scores: list[NodeWithScore],
        top_n: int = 3,
    ) -> list[NodeWithScore]:
        """Rerank candidates for a query and return at most ``top_n`` nodes."""
        if not self.available or not nodes_with_scores:
            return nodes_with_scores[:top_n]

        # Score each query and passage pair together.
        pairs = [(query, node.node.get_content()) for node in nodes_with_scores]
        scores = self.model.predict(pairs)

        # Sort candidates by their cross-encoder scores.
        scored = list(zip(nodes_with_scores, scores))
        scored.sort(key=lambda x: x[1], reverse=True)

        result = []
        for node_with_score, rerank_score in scored[:top_n]:
            # Use the reranker score in the final result.
            node_with_score.score = float(rerank_score)
            result.append(node_with_score)

        return result
