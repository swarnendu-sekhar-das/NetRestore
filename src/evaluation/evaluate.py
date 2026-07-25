"""Evaluate retrieval and optional generation against labelled SOP queries."""

import os
import sys
import json
import argparse
import time
from typing import Sequence

# Add the project root so the src package can be imported.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

def load_ground_truth(path: str) -> list[dict]:
    """Load evaluation Q&A pairs from JSON file."""
    with open(path, "r") as f:
        return json.load(f)


def calculate_document_retrieval_metrics(
    retrieved_file_names: Sequence[Sequence[str]],
    expected_file_names: Sequence[str],
) -> dict:
    """Calculate exact-document ranking metrics without model dependencies."""
    if len(retrieved_file_names) != len(expected_file_names):
        raise ValueError("retrieved_file_names and expected_file_names must have equal lengths")

    total = len(expected_file_names)
    hit_at_1 = 0
    recall_at_3 = 0
    reciprocal_ranks = []

    for results, expected_file_name in zip(retrieved_file_names, expected_file_names):
        normalized_results = [name.lower() for name in results]
        expected = expected_file_name.lower()
        if normalized_results and normalized_results[0] == expected:
            hit_at_1 += 1
        if expected in normalized_results[:3]:
            recall_at_3 += 1
        try:
            reciprocal_ranks.append(1.0 / (normalized_results.index(expected) + 1))
        except ValueError:
            reciprocal_ranks.append(0.0)

    return {
        "exact_document_hit_at_1": hit_at_1 / total if total else 0,
        "exact_document_recall_at_3": recall_at_3 / total if total else 0,
        "mrr": sum(reciprocal_ranks) / total if total else 0,
        "total_queries": total,
    }


def _filters_for_case(qa: dict) -> dict | None:
    """Use explicit test filters when supplied; retain legacy field support."""
    if "filters" in qa:
        return qa["filters"] or None

    filters = {}
    if qa.get("expected_vendor"):
        filters["equipment_vendor"] = qa["expected_vendor"]
    if qa.get("expected_alarm_code"):
        filters["alarm_code"] = qa["expected_alarm_code"]
    return filters or None


def evaluate_retrieval(retriever, qa_pairs: list[dict]) -> dict:
    """
    Evaluate retrieval quality against ground truth.

    Returns:
        Dict with retrieval metrics.
    """
    keyword_hits = 0
    total_keywords = 0
    retrieved_file_names = []
    expected_file_names = []

    print("Retrieval evaluation")

    for i, qa in enumerate(qa_pairs):
        query = qa["query"]
        expected_file_name = qa.get("expected_file_name")
        if not expected_file_name:
            raise ValueError(f"Q{i+1} is missing required expected_file_name")
        expected_keywords = qa.get("expected_keywords", [])
        filters = _filters_for_case(qa)

        # Retrieve documents for the current evaluation case.
        results = retriever.search(query=query, filters=filters if filters else None)

        result_file_names = [r.node.metadata.get("file_name", "") for r in results]
        retrieved_file_names.append(result_file_names)
        expected_file_names.append(expected_file_name)

        # Count expected terms in the retrieved context.
        all_context = " ".join([r.node.get_content().lower() for r in results])
        for kw in expected_keywords:
            total_keywords += 1
            if kw.lower() in all_context:
                keyword_hits += 1

        # Print the result for this case.
        exact_rank = next(
            (rank + 1 for rank, file_name in enumerate(result_file_names)
             if file_name.lower() == expected_file_name.lower()),
            None,
        )
        status = "Pass" if exact_rank else "Fail"
        kw_found = sum(1 for kw in expected_keywords if kw.lower() in all_context)
        print(
            f"{status}: Question {i + 1}: '{query[:60]}' "
            f"Expected SOP: {expected_file_name}. "
            f"Rank: {exact_rank if exact_rank else 'not found'}. "
            f"Keywords: {kw_found}/{len(expected_keywords)}. "
            f"Results: {len(results)}."
        )

    metrics = calculate_document_retrieval_metrics(retrieved_file_names, expected_file_names)
    metrics.update({
        "keyword_hit_rate": keyword_hits / total_keywords if total_keywords > 0 else 0,
    })

    print()
    print(f"Exact document hit at one: {metrics['exact_document_hit_at_1']:.1%}")
    print(f"Exact document recall at three: {metrics['exact_document_recall_at_3']:.1%}")
    print(f"  Keyword Hit Rate (proxy): {metrics['keyword_hit_rate']:.1%} ({keyword_hits}/{total_keywords})")
    print(f"  MRR:               {metrics['mrr']:.3f}")

    return metrics


def evaluate_generation(qa_engine, qa_pairs: list[dict]) -> dict:
    """
    Evaluate generation quality using stateless queries.
    Checks answer completeness (keyword presence) and basic faithfulness.

    Returns:
        Dict with generation metrics.
    """
    total = len(qa_pairs)
    complete_answers = 0
    faithful_answers = 0
    total_latency = 0

    print("Generation evaluation using the Groq LLM")

    for i, qa in enumerate(qa_pairs):
        query = qa["query"]
        expected_keywords = qa.get("expected_keywords", [])
        filters = _filters_for_case(qa)

        try:
            start = time.time()
            response = qa_engine.query_stateless(query, filters=filters)
            latency = time.time() - start
            total_latency += latency

            answer = str(response).lower()

            # Check whether the answer contains enough expected keywords.
            kw_found = sum(1 for kw in expected_keywords if kw.lower() in answer)
            is_complete = kw_found >= len(expected_keywords) * 0.5  # at least 50% of keywords
            if is_complete:
                complete_answers += 1

            # Use a simple response-length and abstention check as a proxy.
            is_faithful = "i cannot find" not in answer and len(answer.strip()) > 50
            if is_faithful:
                faithful_answers += 1

            status = "Pass" if is_complete and is_faithful else "Review"
            print(
                f"{status}: Question {i + 1}: '{query[:50]}' "
                f"Complete: {'yes' if is_complete else 'no'}. "
                f"Faithfulness proxy: {'yes' if is_faithful else 'no'}. "
                f"Latency: {latency:.1f}s. "
                f"Keywords: {kw_found}/{len(expected_keywords)}."
            )

        # Fallback generic exception handler for unexpected API disconnects or generation timeouts
        except Exception as e:
            print(f"Error: Question {i + 1}: '{query[:50]}' {str(e)[:80]}")
            total_latency += 0

    metrics = {
        "answer_completeness": complete_answers / total if total > 0 else 0,
        "faithfulness_rate": faithful_answers / total if total > 0 else 0,
        "avg_latency_seconds": total_latency / total if total > 0 else 0,
        "total_queries": total,
    }

    print()
    print(f"  Answer Completeness: {metrics['answer_completeness']:.1%} ({complete_answers}/{total})")
    print(f"  Faithfulness Rate:   {metrics['faithfulness_rate']:.1%} ({faithful_answers}/{total})")
    print(f"  Avg Latency:         {metrics['avg_latency_seconds']:.2f}s")

    return metrics


def main():
    parser = argparse.ArgumentParser(description="Evaluate NetRestore RAG Pipeline")
    parser.add_argument("--skip-llm", action="store_true",
                        help="Skip LLM generation evaluation (retrieval metrics only)")
    args = parser.parse_args()

    # Define the project paths used by the evaluation.
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    db_path = os.path.join(project_root, "chroma_db")
    qa_path = os.path.join(project_root, "data", "evaluation_qa.json")

    # Load the labelled evaluation cases.
    if not os.path.exists(qa_path):
        print(f"Error: Ground truth file not found: {qa_path}")
        sys.exit(1)

    qa_pairs = load_ground_truth(qa_path)
    print(f"Loaded {len(qa_pairs)} evaluation cases.")

    # Create the retriever used for the evaluation.
    if not os.path.exists(db_path):
        print(f"Error: ChromaDB not found at {db_path}. Run the ingestion script first.")
        sys.exit(1)

    # Keep these imports here so the metric helpers can be tested on their own.
    from src.retrieval.vector_store import TelecomVectorStore
    from src.retrieval.hybrid_search import TelecomHybridRetriever

    vs_manager = TelecomVectorStore(db_path=db_path)
    retriever = TelecomHybridRetriever(vector_store_manager=vs_manager, similarity_top_k=10)

    # Run retrieval evaluation.
    retrieval_metrics = evaluate_retrieval(retriever, qa_pairs)

    # Run generation evaluation only when an API key is available.
    generation_metrics = {}
    if not args.skip_llm:
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            print("Warning: GROQ_API_KEY is not set. Skipping generation evaluation.")
            print("   Set it with: export GROQ_API_KEY=gsk_...")
        else:
            from src.llm.qa_engine import ProceduralQAEngine
            from src.llm.router import SemanticRouter
            from src.llm.topology import NetworkTopologyService
            from src.llm.generator import get_llm_generator

            router = SemanticRouter()
            topology_service = NetworkTopologyService()
            llm = get_llm_generator()
            qa_engine = ProceduralQAEngine(
                retriever_pipeline=retriever,
                router=router,
                topology_service=topology_service,
                llm=llm
            )
            generation_metrics = evaluate_generation(qa_engine, qa_pairs)
    else:
        print("Skipping generation evaluation because --skip-llm was provided.")

    # Print a summary of the collected metrics.
    print("Evaluation summary")
    print("Retrieval metrics")
    print(f"Exact document hit at one: {retrieval_metrics['exact_document_hit_at_1']:.1%}")
    print(f"Exact document recall at three: {retrieval_metrics['exact_document_recall_at_3']:.1%}")
    print(f"Keyword hit rate proxy: {retrieval_metrics['keyword_hit_rate']:.1%}")
    print(f"Mean reciprocal rank: {retrieval_metrics['mrr']:.3f}")

    if generation_metrics:
        print("Generation metrics")
        print(f"Answer completeness: {generation_metrics['answer_completeness']:.1%}")
        print(f"Faithfulness rate: {generation_metrics['faithfulness_rate']:.1%}")
        print(f"Average latency: {generation_metrics['avg_latency_seconds']:.2f}s")

    # Save the metrics for later comparison.
    results_path = os.path.join(project_root, "evaluation_results.json")
    results = {
        "retrieval": retrieval_metrics,
        "generation": generation_metrics,
        "num_qa_pairs": len(qa_pairs),
    }
    with open(results_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"Results saved to {results_path}")


if __name__ == "__main__":
    main()
