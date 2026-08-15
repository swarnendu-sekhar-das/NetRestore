import os
import json
import logging
try:
    from datasets import Dataset
    from ragas import evaluate
    from ragas.metrics import faithfulness, answer_relevancy
except ImportError:
    pass

from src.retrieval.hybrid_search import get_hybrid_retriever
from src.retrieval.vector_store import TelecomVectorStore
from src.llm.qa_engine import ProceduralQAEngine
from src.llm.router import SemanticRouter
from src.llm.topology import NetworkTopologyService
from src.llm.generator import get_llm_generator

logger = logging.getLogger("netrestore")
logging.basicConfig(level=logging.INFO)

def run_evaluation():
    db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "chroma_db"))
    eval_dataset_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "eval_dataset.json"))
    
    if not os.path.exists(eval_dataset_path):
        logger.error(f"Eval dataset not found at {eval_dataset_path}")
        return
        
    with open(eval_dataset_path, "r") as f:
        dataset_records = json.load(f)
        
    vs_manager = TelecomVectorStore(db_path=db_path)
    retriever = get_hybrid_retriever(vs_manager)
    router = SemanticRouter()
    topology_service = NetworkTopologyService()
    llm = get_llm_generator(api_key=os.environ.get("GROQ_API_KEY"))
    
    qa_engine = ProceduralQAEngine(
        retriever_pipeline=retriever,
        router=router,
        topology_service=topology_service,
        llm=llm
    )
    
    questions = []
    answers = []
    contexts = []
    ground_truths = []
    
    hits = 0
    total = min(5, len(dataset_records))
    
    # We will test only the first 5 to save time/API tokens in CI.
    for record in dataset_records[:total]:
        query = record["question"]
        gt_doc = record["expected_document_name"]
        
        questions.append(query)
        ground_truths.append([gt_doc])
        
        try:
            response = qa_engine.query_stateless(query)
            answers.append(str(response))
            
            # Check if the hybrid retriever fetched the exact document we expected
            retrieved_docs = [node.metadata.get("file_name", "") for node in response.source_nodes] if hasattr(response, 'source_nodes') else []
            if gt_doc in retrieved_docs:
                hits += 1
                logger.info(f"✅ HIT: Retrieved {gt_doc}")
            else:
                logger.warning(f"❌ MISS: Expected {gt_doc}, got {retrieved_docs}")
                
            contexts.append(retrieved_docs)
        except Exception as e:
            logger.error(f"Failed query: {e}")
            answers.append("Error")
            contexts.append([])

    logger.info(f"\n--- EVALUATION RESULTS ---")
    logger.info(f"Retriever Accuracy (Hit Rate): {hits}/{total} ({(hits/total)*100:.1f}%)")

    data_dict = {
        "question": questions,
        "answer": answers,
        "contexts": contexts,
        "ground_truth": ground_truths
    }
    
    try:
        eval_dataset = Dataset.from_dict(data_dict)
        logger.info("Executing RAGAS metrics computation...")
        # Note: RAGAS defaults to OpenAI. If OPENAI_API_KEY is not set, we mock completion for CI.
        if "OPENAI_API_KEY" not in os.environ:
            logger.warning("OPENAI_API_KEY not found. Skipping deep RAGAS eval, outputting structure only.")
            logger.info(f"Generated {len(answers)} answers for Golden Dataset.")
            return
            
        result = evaluate(
            eval_dataset,
            metrics=[faithfulness, answer_relevancy]
        )
        print("RAGAS Evaluation Result:", result)
    except Exception as e:
        logger.error(f"Evaluation failed (Likely missing dependencies in test env): {e}")

if __name__ == "__main__":
    run_evaluation()
