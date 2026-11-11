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
    system_prompt = ""
    def chat(self, messages):
        from llama_index.core.llms import ChatResponse, ChatMessage
        return ChatResponse(message=ChatMessage(role="assistant", content="Step 1: Check configurations."))
    def predict(self, prompt, **kwargs):
        return "Step 1: Check configurations."
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
        
        # Known alarm code in context should proceed with procedural synthesis
        response = qa_engine.query("How to fix ALARM_9999 on router XYZ?")
        self.assertNotIsInstance(response, _OutOfScopeResponse)
        self.assertIn("Step 1", str(response))
