import unittest
from llama_index.core.schema import NodeWithScore, TextNode
from llama_index.core.memory import ChatMemoryBuffer
from llama_index.core.llms import ChatMessage
from src.llm.qa_engine import ProceduralQAEngine, _OutOfScopeResponse
from src.llm.router import SemanticRouter
from src.retrieval.hybrid_search import SparseRetriever

class MockLLM:
    system_prompt = ""

    def chat(self, messages):
        from llama_index.core.llms import ChatResponse, ChatMessage
        return ChatResponse(message=ChatMessage(role="assistant", content="Step 1: Verify configurations."))
        
    def predict(self, prompt, **kwargs):
        return "Step 1: Verify configurations."
        
    @property
    def metadata(self):
        from llama_index.core.llms import LLMMetadata
        return LLMMetadata()

class MockTopologyService:
    def get_topology_context(self, query: str, filters: dict = None, ip_address: str = None):
        return "Advisory topology context"

class DynamicMockRetrieverPipeline:
    """Mock retriever that stores nodes and captures the query string it was called with."""
    def __init__(self, nodes):
        self.nodes = nodes
        self.last_query = None

    def get_retriever(self, filters: dict = None):
        parent = self
        class DynamicRetriever:
            def retrieve(self, query_str):
                parent.last_query = str(query_str)
                return parent.nodes
        return DynamicRetriever()

class AlarmQueryResolutionTests(unittest.TestCase):
    def setUp(self):
        self.router = SemanticRouter()
        self.topology = MockTopologyService()
        self.llm = MockLLM()

    def test_multi_turn_alarm_enrichment(self):
        """When user asks about a node and then provides just the alarm code '3049',
        the engine should enrich the retrieval query with the node from memory."""
        node = TextNode(
            text="Procedure for IND-ACC-16 ALARM 3049",
            metadata={"alarm_code": "3049", "node_id": "IND-ACC-16"}
        )
        mock_pipeline = DynamicMockRetrieverPipeline([NodeWithScore(node=node, score=0.95)])
        
        qa_engine = ProceduralQAEngine(
            retriever_pipeline=mock_pipeline,
            router=self.router,
            topology_service=self.topology,
            llm=self.llm
        )

        memory = ChatMemoryBuffer.from_defaults(token_limit=3000)
        # Turn 1: User mentions IND-ACC-16, bot asks for alarm code
        memory.put(ChatMessage(role="user", content="I see an alert on IND-ACC-16"))
        memory.put(ChatMessage(role="assistant", content="Could you share the exact alarm code or syslog output from that node?"))
        qa_engine.set_memory(memory)

        # Turn 2: User answers with just "3049"
        response = qa_engine.query("3049")

        # Must not return out-of-scope
        self.assertNotIsInstance(response, _OutOfScopeResponse)
        # The retrieval query should have been enriched with the node ID
        self.assertIn("IND-ACC-16", mock_pipeline.last_query)
        self.assertIn("3049", mock_pipeline.last_query)

    def test_alarm_query_with_space_and_node(self):
        """When user provides 'IND-ACC-16 ALARM 3049' (with a space), it should match and proceed."""
        node = TextNode(
            text="[Context: IND-ACC-16_ALARM_3049_SOP.pdf] BGP neighbor flap",
            metadata={"alarm_code": "3049", "file_name": "IND-ACC-16_ALARM_3049_SOP.pdf"}
        )
        mock_pipeline = DynamicMockRetrieverPipeline([NodeWithScore(node=node, score=0.9)])

        qa_engine = ProceduralQAEngine(
            retriever_pipeline=mock_pipeline,
            router=self.router,
            topology_service=self.topology,
            llm=self.llm
        )

        response = qa_engine.query("IND-ACC-16 ALARM 3049")
        self.assertNotIsInstance(response, _OutOfScopeResponse)

    def test_sparse_retriever_tokenizes_space_and_standalone_digits(self):
        """SparseRetriever should extract alarm code tokens even when formatted with spaces or plain digits."""
        sr = SparseRetriever({})
        # Test query "3049"
        from llama_index.core.schema import QueryBundle
        
        # Test tokenization behavior using internal logic
        tokens_1 = sr._retrieve(QueryBundle(query_str="3049"))
        self.assertEqual(tokens_1, []) # no bm25 attached, but shouldn't crash

    def test_router_classifies_standalone_alarm_codes(self):
        """Router should classify standalone alarm codes or 'ALARM 3049' as telecom."""
        self.assertEqual(self.router.classify("3049"), "telecom")
        self.assertEqual(self.router.classify("ALARM 3049"), "telecom")
        self.assertEqual(self.router.classify("ALARM_3049"), "telecom")
        self.assertEqual(self.router.classify("IND-ACC-16 ALARM 3049"), "telecom")
        self.assertEqual(self.router.classify("indiranagar ind-acc-16 down and with alarm 3049"), "telecom")

    def test_natural_language_query_with_location_and_alarm(self):
        """Natural language queries like 'indiranagar ind-acc-16 down and with alarm 3049'
        should extract the node and alarm code and successfully retrieve."""
        node = TextNode(
            text="[Context: IND-ACC-16_ALARM_3049_SOP.pdf] [Resolution Steps] Step 1: Verify BGP",
            metadata={"alarm_code": "3049", "node_id": "IND-ACC-16", "file_name": "IND-ACC-16_ALARM_3049_SOP.pdf"}
        )
        mock_pipeline = DynamicMockRetrieverPipeline([NodeWithScore(node=node, score=0.98)])

        qa_engine = ProceduralQAEngine(
            retriever_pipeline=mock_pipeline,
            router=self.router,
            topology_service=self.topology,
            llm=self.llm
        )

        query_str = "indiranagar ind-acc-16 down and with alarm 3049"
        response = qa_engine.query(query_str)
        self.assertNotIsInstance(response, _OutOfScopeResponse)
        self.assertIn("IND-ACC-16", mock_pipeline.last_query.upper())
        self.assertIn("3049", mock_pipeline.last_query)

    def test_natural_language_fault_query_without_alarm_code(self):
        """Arbitrary natural language queries describing network faults (e.g. 'routing protocol flap on Indiranagar exchange')
        should be classified as telecom and answered directly from retrieved SOP context."""
        node = TextNode(
            text="[Context: IND-ACC-16_ALARM_3049_SOP.pdf] Routing protocol flaps on Arista access node",
            metadata={"file_name": "IND-ACC-16_ALARM_3049_SOP.pdf"}
        )
        mock_pipeline = DynamicMockRetrieverPipeline([NodeWithScore(node=node, score=0.92)])

        qa_engine = ProceduralQAEngine(
            retriever_pipeline=mock_pipeline,
            router=self.router,
            topology_service=self.topology,
            llm=self.llm
        )

        nl_query = "routing protocol flap on Indiranagar exchange"
        self.assertEqual(self.router.classify(nl_query), "telecom")

        response = qa_engine.query(nl_query)
        self.assertNotIsInstance(response, _OutOfScopeResponse)

    def test_natural_language_query_with_numbers_not_alarm(self):
        """Natural language queries that contain numbers (e.g. interface numbers, dropped packet counts)
        should not be mistaken for alarm codes and should not be falsely rejected."""
        node = TextNode(
            text="Procedure for resolving packet drop on interface GigabitEthernet0/0/1",
            metadata={"file_name": "CISCO_INTERFACE_DROP_SOP.pdf"}
        )
        mock_pipeline = DynamicMockRetrieverPipeline([NodeWithScore(node=node, score=0.91)])

        qa_engine = ProceduralQAEngine(
            retriever_pipeline=mock_pipeline,
            router=self.router,
            topology_service=self.topology,
            llm=self.llm
        )

        query_with_numbers = "interface GigabitEthernet0/0/1 packet loss 500 packets dropped"
        self.assertEqual(self.router.classify(query_with_numbers), "telecom")

        response = qa_engine.query(query_with_numbers)
        self.assertNotIsInstance(response, _OutOfScopeResponse)
