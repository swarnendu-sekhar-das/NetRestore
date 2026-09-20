"""Connect retrieval, topology context, and the LLM for user questions."""

import os
import json
import re
from llama_index.core.chat_engine import ContextChatEngine
from llama_index.core.memory import ChatMemoryBuffer
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core.schema import NodeWithScore, TextNode
from src.llm.generator import get_llm_generator
from src.llm.prompts import (
    SYSTEM_PROMPT,
    TOPOLOGY_CONTEXT_TEMPLATE,
    OUT_OF_SCOPE_RESPONSE,
    CONTEXT_QA_PROMPT_TMPL,
)


class ProceduralQAEngine:
    """Coordinate retrieval, routing, topology context, and chat memory."""

    def __init__(self, retriever_pipeline, router, topology_service, llm, token_limit: int = 3072):
        """Store the services used to answer a question."""
        self.retriever = retriever_pipeline
        self.router = router
        self.topology_service = topology_service
        self.llm = llm
        self.token_limit = token_limit
        # Streamlit provides session-specific chat memory.
        self.memory = None

    def set_memory(self, memory: ChatMemoryBuffer):
        """Set the chat memory for the current Streamlit session."""
        self.memory = memory

    def query(self, query_str: str, filters: dict = None):
        """Answer a conversational query with the current filters and memory."""
        # Keep follow-up questions inside the telecom scope.
        has_memory = self.memory is not None and len(self.memory.get_all()) > 0
        query_type = self.router.classify(query_str, has_memory=has_memory)
        
        if query_type == "general":
            # Return early for questions outside the supported scope.
            return _OutOfScopeResponse(OUT_OF_SCOPE_RESPONSE)

        # Extract Syslog IP via SemanticRouter
        extracted_ip = self.router.extract_ip(query_str)

        # Add static topology context when a matching node or IP is present.
        topology_ctx = self.topology_service.get_topology_context(query_str, filters, ip_address=extracted_ip)
        topology_suffix = ""
        if topology_ctx:
            topology_suffix = TOPOLOGY_CONTEXT_TEMPLATE.format(topology_context=topology_ctx)

        # Combine the base prompt with any topology context.
        full_system_prompt = SYSTEM_PROMPT + topology_suffix

        base_retriever = self.retriever.get_retriever(filters)

        # Add strict unknown-alarm/no-answer behavior
        alarm_match = re.search(r'ALARM(?:_CODE)?_(\d+)', query_str, re.IGNORECASE)
        if alarm_match:
            alarm_code = alarm_match.group(1)
            # Retrieve nodes to verify if the alarm code is present in context
            try:
                retrieved_nodes = base_retriever.retrieve(query_str)
                has_alarm = False
                for node_with_score in retrieved_nodes:
                    node_text = node_with_score.node.get_content().upper()
                    meta = node_with_score.node.metadata
                    
                    if str(meta.get("alarm_code", "")) == alarm_code:
                        has_alarm = True
                        break
                        
                    # Check text as fallback
                    if f"ALARM_{alarm_code}" in node_text or f"ALARM_CODE_{alarm_code}" in node_text:
                        has_alarm = True
                        break
                        
                if not has_alarm:
                    return _OutOfScopeResponse("I cannot find the procedure for this in the provided Methods of Procedure.")
            except Exception as e:
                # If retrieval fails here, let the chat engine try or fallback normally
                pass

        # Use session memory when available.
        memory = self.memory or ChatMemoryBuffer.from_defaults(
            token_limit=self.token_limit
        )

        chat_engine = ContextChatEngine.from_defaults(
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

        response = chat_engine.chat(query_str)
        return response

    def query_stateless(self, query_str: str, filters: dict = None):
        """Answer one query without chat memory for evaluation scripts."""
        # Extract Syslog IP via SemanticRouter
        extracted_ip = self.router.extract_ip(query_str)

        # Add static topology context when a matching node or IP is present.
        topology_ctx = self.topology_service.get_topology_context(query_str, filters, ip_address=extracted_ip)
        topology_suffix = ""
        if topology_ctx:
            topology_suffix = TOPOLOGY_CONTEXT_TEMPLATE.format(topology_context=topology_ctx)

        # Create a dynamic prompt with topology context just for this query
        from llama_index.core import PromptTemplate
        dynamic_prompt = PromptTemplate(CONTEXT_QA_PROMPT_TMPL + topology_suffix)

        base_retriever = self.retriever.get_retriever(filters)

        engine = RetrieverQueryEngine.from_args(
            retriever=base_retriever,
            llm=self.llm,
            text_qa_template=dynamic_prompt
        )

        response = engine.query(query_str)
        return response


class _OutOfScopeResponse:
    """Small response object used for out-of-scope questions."""

    def __init__(self, message: str):
        self.response = message
        self.source_nodes = []

    def __str__(self):
        return self.response
