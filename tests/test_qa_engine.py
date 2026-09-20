import unittest
from llama_index.core.memory import ChatMemoryBuffer
from src.llm.qa_engine import ProceduralQAEngine

class DummyRouter:
    def classify(self, query: str, has_memory: bool = False):
        return "telecom"
    def extract_ip(self, query: str):
        return ""

class DummyTopologyService:
    def get_topology_context(self, query: str, filters: dict = None, ip_address: str = None):
        return ""

class DummyRetrieverPipeline:
    def get_retriever(self, filters: dict = None):
        class DummyRetriever:
            def retrieve(self, query_str):
                return []
        return DummyRetriever()

class DummyLLM:
    def chat(self, messages):
        from llama_index.core.llms import ChatResponse, ChatMessage
        # Mock simple echo response
        return ChatResponse(message=ChatMessage(role="assistant", content=f"Mock response to: {messages[-1].content}"))
        
    @property
    def metadata(self):
        from llama_index.core.llms import LLMMetadata
        return LLMMetadata()

class QaEngineSessionTests(unittest.TestCase):
    def test_sessions_are_isolated(self):
        retriever = DummyRetrieverPipeline()
        router = DummyRouter()
        topology = DummyTopologyService()
        llm = DummyLLM()
        
        qa_engine = ProceduralQAEngine(
            retriever_pipeline=retriever,
            router=router,
            topology_service=topology,
            llm=llm
        )
        
        mem1 = ChatMemoryBuffer.from_defaults(token_limit=1000)
        mem2 = ChatMemoryBuffer.from_defaults(token_limit=1000)
        
        # Query on session 1
        qa_engine.set_memory(mem1)
        qa_engine.query("Hello Session 1")
        
        # Query on session 2
        qa_engine.set_memory(mem2)
        qa_engine.query("Hello Session 2")
        
        # Check that memories are separate
        hist1 = mem1.get_all()
        hist2 = mem2.get_all()
        
        # Memory 1 should only have Session 1 interactions
        self.assertTrue(any("Hello Session 1" in m.content for m in hist1))
        self.assertFalse(any("Hello Session 2" in m.content for m in hist1))
        
        # Memory 2 should only have Session 2 interactions
        self.assertTrue(any("Hello Session 2" in m.content for m in hist2))
        self.assertFalse(any("Hello Session 1" in m.content for m in hist2))
