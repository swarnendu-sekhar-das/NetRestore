import os
import sys
import logging
from typing import Optional, Dict, Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from dotenv import load_dotenv
from llama_index.core.memory import ChatMemoryBuffer

# Load environment variables first
load_dotenv()

# Ensure we can import from src
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from src.retrieval.vector_store import TelecomVectorStore
from src.retrieval.hybrid_search import TelecomHybridRetriever
from src.llm.qa_engine import ProceduralQAEngine
from src.llm.router import SemanticRouter
from src.llm.topology import NetworkTopologyService
from src.llm.generator import get_llm_generator
from src.api.middleware import JSONLoggingMiddleware, logger

app = FastAPI(title="NetRestore API", version="1.0.0")
app.add_middleware(JSONLoggingMiddleware)

class AskRequest(BaseModel):
    question: str
    filters: Optional[Dict[str, Any]] = None
    session_id: str

# Global State
vector_store = None
hybrid_retriever = None
router = None
topology_service = None
llm = None
qa_engine = None

# In-memory dictionary for chat memory state management
chat_sessions: Dict[str, ChatMemoryBuffer] = {}

@app.on_event("startup")
def startup_event():
    global vector_store, hybrid_retriever, router, topology_service, llm, qa_engine
    
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        logger.error("Configuration Error: GROQ_API_KEY is not found in the environment.")

    db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "chroma_db"))
    
    if os.path.exists(db_path):
        vector_store = TelecomVectorStore(db_path=db_path)
        from src.retrieval.hybrid_search import get_hybrid_retriever
        hybrid_retriever = get_hybrid_retriever(vector_store)
        router = SemanticRouter()
        topology_service = NetworkTopologyService()
        
        if api_key:
            llm = get_llm_generator(api_key=api_key)
            qa_engine = ProceduralQAEngine(
                retriever_pipeline=hybrid_retriever,
                router=router,
                topology_service=topology_service,
                llm=llm
            )
    else:
        logger.warning(f"Vector Database not found at {db_path} during startup.")

@app.get("/health")
async def health():
    checks = {"status": "healthy"}
    
    # Check ChromaDB connectivity
    try:
        if vector_store and hasattr(vector_store, 'chroma_collection'):
            vector_store.chroma_collection.count()
            checks["chromadb"] = "connected"
        else:
            checks["chromadb"] = "unreachable"
            checks["status"] = "degraded"
    except Exception as e:
        logger.error(f"ChromaDB health check failed: {e}")
        checks["chromadb"] = "unreachable"
        checks["status"] = "degraded"
    
    # Check BM25 index loaded
    try:
        checks["bm25_loaded"] = (
            hybrid_retriever is not None and 
            hybrid_retriever.sparse_retriever is not None and 
            hybrid_retriever.sparse_retriever.bm25 is not None
        )
        if not checks["bm25_loaded"]:
            checks["status"] = "degraded"
    except Exception as e:
        logger.error(f"BM25 health check failed: {e}")
        checks["bm25_loaded"] = False
        checks["status"] = "degraded"
        
    status_code = 200 if checks["status"] == "healthy" else 503
    return JSONResponse(content=checks, status_code=status_code)

@app.post("/ask")
async def ask(request: AskRequest):
    if not qa_engine or not hybrid_retriever:
        raise HTTPException(status_code=503, detail="AI services not initialized. Check server logs.")

    # Get or create chat memory for this session
    if request.session_id not in chat_sessions:
        chat_sessions[request.session_id] = ChatMemoryBuffer.from_defaults(token_limit=3072)
    
    qa_engine.set_memory(chat_sessions[request.session_id])
    
    try:
        response = qa_engine.query(request.question, filters=request.filters)
        
        source_data = []
        if hasattr(response, 'source_nodes') and response.source_nodes:
            for node in response.source_nodes:
                source_data.append({
                    "file_name": node.node.metadata.get('file_name', 'Unknown'),
                    "header": node.node.metadata.get('header_path', 'No Header'),
                    "score": node.score if node.score is not None else 0.0,
                    "text": node.node.get_content()
                })
        
        return {
            "answer": str(response),
            "sources": source_data,
            "fallback": False
        }
    except Exception as e:
        logger.error(f"LLM generation failed: {e}")
        
        # Fallback: Retrieve chunks directly and return them raw
        try:
            retrieved_chunks = hybrid_retriever.search(request.question, request.filters)
            raw_context = "\n---\n".join([chunk.node.get_content() for chunk in retrieved_chunks[:3]])
            
            source_data = []
            for chunk in retrieved_chunks[:3]:
                source_data.append({
                    "file_name": chunk.node.metadata.get('file_name', 'Unknown'),
                    "header": chunk.node.metadata.get('header_path', 'No Header'),
                    "score": chunk.score if chunk.score is not None else 0.0,
                    "text": chunk.node.get_content()
                })
                
            return {
                "answer": f"⚠️ AI generation is temporarily unavailable. Here are the relevant SOP sections:\n\n{raw_context}",
                "sources": source_data,
                "fallback": True
            }
        except Exception as fallback_err:
            logger.error(f"Fallback retrieval also failed: {fallback_err}")
            raise HTTPException(status_code=500, detail="An error occurred while generating the response and fallback failed.")
