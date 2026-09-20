import os
import json
import logging
import sys

# Add the project root to PYTHONPATH so we can import from src
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from types import ModuleType
sys.modules["langchain_community.chat_models"] = ModuleType("langchain_community.chat_models")
sys.modules["langchain_community.chat_models.vertexai"] = ModuleType("langchain_community.chat_models.vertexai")
sys.modules["langchain_community.chat_models.vertexai"].ChatVertexAI = None

try:
    from datasets import Dataset
    from ragas import evaluate
    from ragas.metrics import Faithfulness, AnswerRelevancy
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
    
    hits_at_1 = 0
    hits_at_3 = 0
    hits_at_10 = 0
    total = min(9, len(dataset_records)) # test a few more to include edge cases
    
    # We will test only the first few to save time/API tokens in CI.
    for record in dataset_records[:total]:
        query = record["question"]
        gt_doc = record["expected_document_name"]
        
        questions.append(query)
        ground_truths.append(gt_doc)  # Ragas 0.3+ requires a string, not a list of strings
        
        try:
            response = qa_engine.query_stateless(query)
            answers.append(str(response))
            
            # Check if the hybrid retriever fetched the exact document we expected
            retrieved_filenames = [node.metadata.get("file_name", "") for node in response.source_nodes] if hasattr(response, 'source_nodes') else []
            
            if gt_doc == "NONE":
                if not retrieved_filenames or "cannot find the procedure" in str(response).lower() or "i'm a specialized network support assistant" in str(response).lower():
                    hits_at_1 += 1
                    hits_at_3 += 1
                    hits_at_10 += 1
                    logger.info(f"✅ HIT: Handled out-of-scope/unknown correctly")
                else:
                    logger.warning(f"❌ MISS: Expected out-of-scope, got {retrieved_filenames}")
            else:
                if gt_doc in retrieved_filenames[:1]:
                    hits_at_1 += 1
                if gt_doc in retrieved_filenames[:3]:
                    hits_at_3 += 1
                if gt_doc in retrieved_filenames[:10]:
                    hits_at_10 += 1
                    
                if gt_doc in retrieved_filenames[:10]:
                    logger.info(f"✅ HIT: Retrieved {gt_doc}")
                else:
                    logger.warning(f"❌ MISS: Expected {gt_doc}, got {retrieved_filenames}")
                
            # RAGAS requires the actual text context to compute Faithfulness, not just filenames.
            node_texts = [node.get_content() for node in response.source_nodes] if hasattr(response, 'source_nodes') else []
            
            # Since we inject Topology into the prompt dynamically, we must also append it to the RAGAS context
            # so the 120B Judge knows the LLM didn't hallucinate the network nodes.
            extracted_ip = qa_engine.router.extract_ip(query)
            topo_ctx = qa_engine.topology_service.get_topology_context(query, ip_address=extracted_ip)
            if topo_ctx:
                node_texts.append("--- NETWORK TOPOLOGY CONTEXT ---\n" + topo_ctx)
                
            contexts.append(node_texts)
        except Exception as e:
            logger.error(f"Failed query: {e}")
            answers.append("Error")
            contexts.append([])

    logger.info(f"\n--- EVALUATION RESULTS ---")
    logger.info(f"Recall@1: {hits_at_1}/{total} ({(hits_at_1/total)*100:.1f}%)")
    logger.info(f"Recall@3: {hits_at_3}/{total} ({(hits_at_3/total)*100:.1f}%)")
    logger.info(f"Recall@10: {hits_at_10}/{total} ({(hits_at_10/total)*100:.1f}%)")

    data_dict = {
        "question": questions,
        "answer": answers,
        "contexts": contexts,
        "ground_truth": ground_truths
    }
    
    try:
        eval_dataset = Dataset.from_dict(data_dict)
        logger.info("Executing RAGAS metrics computation...")
            
        from openai import OpenAI
        from ragas.llms import llm_factory
        from ragas.embeddings import HuggingFaceEmbeddings
        
        # Configure the judge LLM to use a fast, high-context model to avoid timeouts on massive text payloads
        # We use the OpenAI client since Groq exposes an OpenAI-compatible API
        groq_client = OpenAI(
            api_key=os.environ.get("GROQ_API_KEY"),
            base_url="https://api.groq.com/openai/v1"
        )
        ragas_llm = llm_factory(model="openai/gpt-oss-120b", client=groq_client)
        
        # Configure the embeddings using langchain-huggingface which exposes the
        # embed_query interface required by AnswerRelevancy metric
        from langchain_huggingface import HuggingFaceEmbeddings as LCHFEmbeddings
        from ragas.embeddings import LangchainEmbeddingsWrapper
        lc_emb = LCHFEmbeddings(model_name="all-MiniLM-L6-v2")
        ragas_emb = LangchainEmbeddingsWrapper(lc_emb)
        
        result = evaluate(
            eval_dataset,
            metrics=[Faithfulness(), AnswerRelevancy()],
            llm=ragas_llm,
            embeddings=ragas_emb
        )
        print("RAGAS Evaluation Result:", result)
    except Exception as e:
        logger.error(f"Evaluation failed (Likely missing dependencies in test env): {e}")

if __name__ == "__main__":
    run_evaluation()
