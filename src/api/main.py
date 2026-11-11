import os
import sys
import time
import asyncio
import logging
from typing import Optional, Dict, Any
from collections import OrderedDict

from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
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

class AskRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=1000, description="User query or syslog message")
    filters: Optional[Dict[str, Any]] = None
    session_id: str = Field(..., min_length=1, max_length=128, description="Client session identifier")

# Global State
vector_store = None
hybrid_retriever = None
router = None
topology_service = None
llm = None
qa_engine = None


@asynccontextmanager
async def lifespan(app_instance: FastAPI):
    """Modern lifespan handler for graceful initialization and cleanup."""
    global vector_store, hybrid_retriever, router, topology_service, llm, qa_engine

    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        logger.error("Configuration Error: GROQ_API_KEY is not found in the environment.")

    db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "chroma_db"))
    bm25_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "shared_data", "bm25_index.pkl"))

    if os.path.exists(db_path):
        vector_store = TelecomVectorStore(db_path=db_path)
        from src.retrieval.hybrid_search import get_hybrid_retriever
        hybrid_retriever = get_hybrid_retriever(vector_store, bm25_path=bm25_path)
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

    yield


app = FastAPI(title="NetRestore API", version="1.0.0", lifespan=lifespan)
app.add_middleware(JSONLoggingMiddleware)


class BoundedSessionStore:
    """In-memory session buffer store with TTL and LRU eviction to prevent unbounded memory growth."""
    def __init__(self, max_size: int = 500, ttl_seconds: int = 3600):
        self.sessions: OrderedDict[str, ChatMemoryBuffer] = OrderedDict()
        self.timestamps: Dict[str, float] = {}
        self.max_size = max_size
        self.ttl = ttl_seconds

    def get_or_create(self, session_id: str, token_limit: int = 3072) -> ChatMemoryBuffer:
        now = time.time()
        if session_id in self.sessions:
            if now - self.timestamps.get(session_id, 0) < self.ttl:
                self.sessions.move_to_end(session_id)
                self.timestamps[session_id] = now
                return self.sessions[session_id]
            else:
                # Session expired; evict
                del self.sessions[session_id]
                self.timestamps.pop(session_id, None)

        if len(self.sessions) >= self.max_size:
            oldest_id, _ = self.sessions.popitem(last=False)
            self.timestamps.pop(oldest_id, None)

        new_memory = ChatMemoryBuffer.from_defaults(token_limit=token_limit)
        self.sessions[session_id] = new_memory
        self.timestamps[session_id] = now
        return new_memory

    def __contains__(self, session_id: str) -> bool:
        return session_id in self.sessions

    def __getitem__(self, session_id: str) -> ChatMemoryBuffer:
        return self.sessions[session_id]

    def __setitem__(self, session_id: str, mem: ChatMemoryBuffer):
        self.sessions[session_id] = mem
        self.timestamps[session_id] = time.time()


# In-memory session store with TTL eviction
chat_sessions = BoundedSessionStore(max_size=300, ttl_seconds=3600)

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

    # Retrieve bounded session memory (prevents unbounded memory leak)
    session_memory = chat_sessions.get_or_create(request.session_id)
    
    try:
        # Offload synchronous retrieval and inference to worker thread pool
        # This keeps FastAPI's single asyncio event loop free to handle health checks and concurrent requests
        response = await asyncio.to_thread(
            qa_engine.query,
            request.question,
            filters=request.filters,
            memory=session_memory
        )
        
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
            retrieved_chunks = await asyncio.to_thread(hybrid_retriever.search, request.question, request.filters)
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
