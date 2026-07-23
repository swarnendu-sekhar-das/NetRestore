"""
Procedural QA Engine with Topology-Aware Reasoning and Query Routing.

This is the central orchestration class that ties together:
  - Hybrid retrieval (BM25 + vector + reranker)
  - Network topology injection (cascade analysis)
  - Query routing (in-scope vs out-of-scope)
  - Chat memory (conversational continuity)
  - LLM generation with chain-of-thought reasoning
"""

import os
import json
from llama_index.core.chat_engine import ContextChatEngine
from llama_index.core.memory import ChatMemoryBuffer
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core.schema import NodeWithScore, TextNode
from src.llm.generator import get_llm_generator
from src.llm.prompts import (
    SYSTEM_PROMPT,
    TOPOLOGY_CONTEXT_TEMPLATE,
    OUT_OF_SCOPE_RESPONSE,
    procedural_qa_prompt,
    legacy_procedural_qa_prompt,
)


# The router and topology logic have been extracted to adhere to SRP and OCP.


class ProceduralQAEngine:
    """
    Ties together the Hybrid Retriever, Chat Memory, Network Topology,
    and the LLM into a cohesive conversational QA pipeline with
    chain-of-thought reasoning and query routing.

    Supports two modes:
    - Conversational (default): Uses ContextChatEngine with ChatMemoryBuffer for
      multi-turn chat with CoT reasoning. Follow-up questions are contextual.
    - Legacy/stateless: Falls back to RetrieverQueryEngine for single-shot QA
      (used by test scripts).
    """

    def __init__(self, retriever_pipeline, router, topology_service, llm, token_limit: int = 3072):
        """
        Expects dependencies to be injected (Dependency Inversion Principle).
        
        Args:
            retriever_pipeline: TelecomHybridRetriever instance
            router: SemanticRouter instance
            topology_service: NetworkTopologyService instance
            llm: Generator instance
            token_limit: Maximum tokens for the chat memory sliding window.
        """
        self.retriever = retriever_pipeline
        self.router = router
        self.topology_service = topology_service
        self.llm = llm
        self.token_limit = token_limit
        # Chat memory will be managed per-session (set externally by Streamlit)
        self.memory = None

    def set_memory(self, memory: ChatMemoryBuffer):
        """
        Allow external code (e.g. Streamlit session state) to inject a
        session-specific ChatMemoryBuffer for conversational continuity.
        """
        self.memory = memory

    def query(self, query_str: str, filters: dict = None):
        """
        Conversational query with chain-of-thought + persistent memory
        + topology awareness + query routing.

        The ContextChatEngine is reused across calls (stored as self._chat_engine)
        so that ChatMemoryBuffer genuinely accumulates all previous turns.
        It is only rebuilt when the filters change (new vendor/alarm selection).

        Returns a response object with .response (text) and .source_nodes (citations).
        """
        # ── Query Routing ──
        # Check if we have active conversational context to bypass strict filtering
        has_memory = self.memory is not None and len(self.memory.get_all()) > 0
        query_type = self.router.classify(query_str, has_memory=has_memory)
        
        if query_type == "general":
            # Return a polite out-of-scope response without wasting retrieval/LLM resources
            return _OutOfScopeResponse(OUT_OF_SCOPE_RESPONSE)

        # ── Build topology context ──
        topology_ctx = self.topology_service.get_topology_context(query_str, filters)
        topology_suffix = ""
        if topology_ctx:
            topology_suffix = TOPOLOGY_CONTEXT_TEMPLATE.format(topology_context=topology_ctx)

        # Full system prompt = base CoT prompt + topology context
        full_system_prompt = SYSTEM_PROMPT + topology_suffix

        # Only rebuild the chat engine when filters change, preserving memory otherwise
        filters_key = str(sorted(filters.items())) if filters else "none"
        if not hasattr(self, '_chat_engine') or self._filters_key != filters_key:
            self._filters_key = filters_key
            base_retriever = self.retriever.get_retriever(filters)

            # Use injected session memory, or create a fresh one for single calls
            memory = self.memory or ChatMemoryBuffer.from_defaults(
                token_limit=self.token_limit
            )

            self._chat_engine = ContextChatEngine.from_defaults(
                retriever=base_retriever,
                llm=self.llm,
                memory=memory,
                system_prompt=full_system_prompt,
                context_template=(
                    "Here are the relevant SOP documents retrieved for this query:\n"
                    "---------------------\n"
                    "{context_str}\n"
                    "---------------------\n"
                ),
            )
        else:
            # Filters unchanged — update system prompt for topology freshness
            # (topology context may change based on query content even with same filters)
            self._chat_engine._prefix_messages[0].content = full_system_prompt

        response = self._chat_engine.chat(query_str)
        return response

    def query_stateless(self, query_str: str, filters: dict = None):
        """
        Legacy stateless query (no memory, no CoT).
        Used by test scripts and evaluation notebooks for deterministic results.
        """
        base_retriever = self.retriever.get_retriever(filters)

        engine = RetrieverQueryEngine.from_args(
            retriever=base_retriever,
            llm=self.llm,
            text_qa_template=legacy_procedural_qa_prompt
        )

        response = engine.query(query_str)
        return response


class _OutOfScopeResponse:
    """
    Lightweight response object for out-of-scope queries.
    Mimics the LlamaIndex response interface so main.py doesn't break.
    """

    def __init__(self, message: str):
        self.response = message
        self.source_nodes = []

    def __str__(self):
        return self.response
