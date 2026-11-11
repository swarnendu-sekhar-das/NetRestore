import time
import unittest
from llama_index.core.memory import ChatMemoryBuffer
from llama_index.core.llms import ChatMessage
from llama_index.core.schema import TextNode, NodeWithScore

from src.retrieval.tokenizer import telecom_tokenize
from src.llm.router import SemanticRouter
from src.llm.topology import NetworkTopologyService
from src.api.main import BoundedSessionStore
from src.llm.qa_engine import ProceduralQAEngine, _OutOfScopeResponse


class RemediationUnitTests(unittest.TestCase):
    """Unit tests verifying fixes for Tier 1 and Tier 2 issues."""

    def test_tokenizer_telecom_extraction(self):
        """Verify centralized tokenizer extracts node IDs, alarm codes, and keywords."""
        sample_text = "Router IND-ACC-16 has ALARM_3049 triggered with CRC error on port TenGigE0/1/1"
        tokens = telecom_tokenize(sample_text)

        # Node ID should be lowercase token
        self.assertIn("ind-acc-16", tokens)
        # Alarm code should be extracted both as 'alarm_3049' and '3049'
        self.assertIn("alarm_3049", tokens)
        self.assertIn("3049", tokens)
        # Domain keywords extracted
        self.assertIn("crc", tokens)
        self.assertIn("error", tokens)
        # Common stopwords excluded
        self.assertNotIn("has", tokens)
        self.assertNotIn("with", tokens)
        self.assertNotIn("on", tokens)

    def test_router_word_boundary_matching(self):
        """Verify router does not falsely trigger on substring overlaps like 'airport' for 'port'."""
        router = SemanticRouter()

        # 'airport' contains 'port', but should NOT be classified as telecom
        self.assertEqual(router.classify("Flight arrival at the international airport"), "general")
        
        # Exact keyword 'port' or telecom sentence should be classified as telecom
        self.assertEqual(router.classify("Check status of interface port 4"), "telecom")
        self.assertEqual(router.classify("BGP peer session went down"), "telecom")

    def test_topology_neighbor_formatting(self):
        """Verify vendor-level topology context outputs actual neighbor node IDs instead of 'None'."""
        topology_service = NetworkTopologyService()
        
        # Test vendor context for Juniper routers
        context = topology_service.get_topology_context("What are the Juniper devices?", filters={"equipment_vendor": "Juniper"})
        
        self.assertIn("Affected Vendor: Juniper", context)
        # Must NOT contain 'Connected to: None' when nodes have neighbors in topology JSON
        self.assertNotIn("Connected to: None", context)
        # Should contain actual neighbor connection references
        self.assertIn("Connected to:", context)

    def test_bounded_session_store_capacity_and_ttl(self):
        """Verify BoundedSessionStore enforces max capacity and expires stale sessions."""
        store = BoundedSessionStore(max_size=3, ttl_seconds=1)

        mem1 = store.get_or_create("session_1")
        mem2 = store.get_or_create("session_2")
        mem3 = store.get_or_create("session_3")

        self.assertIn("session_1", store)
        self.assertIn("session_2", store)
        self.assertIn("session_3", store)

        # Access session_1 to make it most recently used
        store.get_or_create("session_1")

        # Adding a 4th session should evict the oldest unaccessed session (session_2)
        store.get_or_create("session_4")
        self.assertIn("session_1", store)
        self.assertNotIn("session_2", store)
        self.assertIn("session_4", store)

        # Test TTL expiration
        time.sleep(1.1)
        # Getting session_1 after TTL should return a new fresh buffer, not the old one
        new_mem1 = store.get_or_create("session_1")
        self.assertIsNot(mem1, new_mem1)

    def test_stateless_qa_engine_memory_isolation(self):
        """Verify that ProceduralQAEngine.query uses explicitly passed memory without cross-talk."""
        class MockLLM:
            system_prompt = ""
            def chat(self, messages):
                from llama_index.core.llms import ChatResponse, ChatMessage
                return ChatResponse(message=ChatMessage(role="assistant", content="Step 1: Check neighbor."))
            def predict(self, prompt, **kwargs):
                return "Step 1: Check neighbor."
            @property
            def metadata(self):
                from llama_index.core.llms import LLMMetadata
                return LLMMetadata()

        class DummyRetrieverPipeline:
            def get_retriever(self, filters=None):
                node = TextNode(
                    text="Procedure for IND-ACC-16 ALARM 3049",
                    metadata={"alarm_code": "3049", "node_id": "IND-ACC-16", "file_name": "sop_3049.pdf"}
                )
                class DummyRetriever:
                    def retrieve(self, q):
                        return [NodeWithScore(node=node, score=0.9)]
                return DummyRetriever()

        router = SemanticRouter()
        topology = NetworkTopologyService()
        llm = MockLLM()
        qa_engine = ProceduralQAEngine(DummyRetrieverPipeline(), router, topology, llm)

        # Create two distinct sessions
        mem_a = ChatMemoryBuffer.from_defaults(token_limit=1000)
        mem_a.put(ChatMessage(role="user", content="Alert on IND-ACC-16"))

        mem_b = ChatMemoryBuffer.from_defaults(token_limit=1000)
        mem_b.put(ChatMessage(role="user", content="Alert on BLR-CORE-01"))

        # Query passing mem_a explicitly
        resp_a = qa_engine.query("3049", memory=mem_a)
        self.assertNotIsInstance(resp_a, _OutOfScopeResponse)

        # Assert qa_engine's instance memory was not mutated (retains thread safety)
        self.assertIsNone(qa_engine.memory)


if __name__ == "__main__":
    unittest.main()
