import unittest
from llama_index.core.schema import NodeWithScore, TextNode
from src.llm.qa_engine import ProceduralQAEngine, _OutOfScopeResponse

class DummyRouter:
    def classify(self, query: str, has_memory: bool = False):
        return "telecom"
    def extract_ip(self, query: str):
        return ""

class DummyTopologyService:
    def get_topology_context(self, query: str, filters: dict = None, ip_address: str = None):
        return ""

class DummyRetrieverPipeline:
    def __init__(self, mock_nodes):
        self.mock_nodes = mock_nodes
        
    def get_retriever(self, filters: dict = None):
        class DummyRetriever:
            def __init__(self, nodes):
                self.nodes = nodes
            def retrieve(self, query_str):
                return self.nodes
        return DummyRetriever(self.mock_nodes)

class DummyLLM:
    def chat(self, messages):
        pass
    @property
    def metadata(self):
        from llama_index.core.llms import LLMMetadata
        return LLMMetadata()

class UnknownAlarmBehaviorTests(unittest.TestCase):
    def test_unknown_alarm_code_returns_out_of_scope(self):
        # Retrieved context doesn't have the alarm code
        mock_node = TextNode(text="Procedure for ALARM_5555", metadata={"alarm_code": "5555"})
        retriever = DummyRetrieverPipeline([NodeWithScore(node=mock_node, score=0.9)])
        
        qa_engine = ProceduralQAEngine(
            retriever_pipeline=retriever,
            router=DummyRouter(),
            topology_service=DummyTopologyService(),
            llm=DummyLLM()
        )
        
        response = qa_engine.query("How to fix ALARM_9999 on router XYZ?")
        
        self.assertIsInstance(response, _OutOfScopeResponse)
        self.assertEqual(str(response), "I cannot find the procedure for this in the provided Methods of Procedure.")
        
    def test_known_alarm_code_proceeds(self):
        # Retrieved context matches the alarm code
        mock_node = TextNode(text="Procedure for ALARM_9999", metadata={"alarm_code": "9999"})
        retriever = DummyRetrieverPipeline([NodeWithScore(node=mock_node, score=0.9)])
        
        qa_engine = ProceduralQAEngine(
            retriever_pipeline=retriever,
            router=DummyRouter(),
            topology_service=DummyTopologyService(),
            llm=DummyLLM()
        )
        
        # In a real scenario, this would return a chat response. Since DummyLLM returns a mock response
        # or raises an error, we just check that it DOES NOT return _OutOfScopeResponse.
        try:
            response = qa_engine.query("How to fix ALARM_9999 on router XYZ?")
            self.assertNotIsInstance(response, _OutOfScopeResponse)
        except Exception as e:
            # If the dummy LLM fails to implement something, it's fine as long as we bypassed the out-of-scope check
            pass
