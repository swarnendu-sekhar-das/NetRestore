"""Connect retrieval, topology context, and the LLM for user questions."""

import os
import json
import re
from llama_index.core.chat_engine import ContextChatEngine
from llama_index.core.memory import ChatMemoryBuffer
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core.response_synthesizers import get_response_synthesizer, ResponseMode
from llama_index.core.retrievers import BaseRetriever
from llama_index.core.schema import NodeWithScore, TextNode, QueryBundle
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

    def query(self, query_str: str, filters: dict = None, memory: ChatMemoryBuffer = None):
        """Answer a conversational query with the current filters and memory."""
        # Use session-passed memory to avoid global singleton race conditions; fallback to self.memory
        active_memory = memory if memory is not None else self.memory
        has_memory = active_memory is not None and len(active_memory.get_all()) > 0
        query_type = self.router.classify(query_str, has_memory=has_memory)
        
        if query_type == "general":
            # Return early for questions outside the supported scope.
            return _OutOfScopeResponse(OUT_OF_SCOPE_RESPONSE)

        # Extract Syslog IP via SemanticRouter
        extracted_ip = self.router.extract_ip(query_str)

        # Multi-turn context resolution:
        # If query lacks a node ID, resolve the most recently mentioned node ID from chat memory
        is_node_ref_fn = getattr(self.router, "is_node_reference", None)
        node_id_in_query = is_node_ref_fn(query_str) if is_node_ref_fn else False
        recent_node_id = None
        node_re = getattr(self.router, "_NODE_ID_RE", None)
        if not node_id_in_query and has_memory and node_re:
            for msg in reversed(active_memory.get_all()):
                node_match = node_re.search(msg.content)
                if node_match:
                    recent_node_id = node_match.group(0).upper()
                    break

        # Build effective topology query so topology context is retrieved even in follow-up answers (e.g. "3049")
        effective_topology_query = query_str if (node_id_in_query or not recent_node_id) else f"{recent_node_id} {query_str}"
        topology_ctx = self.topology_service.get_topology_context(effective_topology_query, filters, ip_address=extracted_ip)
        topology_suffix = ""
        if topology_ctx:
            topology_suffix = TOPOLOGY_CONTEXT_TEMPLATE.format(topology_context=topology_ctx)

        # Combine the base prompt with any topology context.
        full_system_prompt = SYSTEM_PROMPT + topology_suffix

        # Extract alarm code flexibly: e.g. ALARM_3049, ALARM 3049, ALARM CODE 3049, or standalone digits
        alarm_match = re.search(r'\bALARM(?:[_\s-]*(?:CODE)?[_\s-]*)?(\d+)\b', query_str, re.IGNORECASE)
        alarm_code = None
        if alarm_match:
            alarm_code = alarm_match.group(1)
        elif query_str.strip().isdigit() and 3 <= len(query_str.strip()) <= 5:
            alarm_code = query_str.strip()

        # Build retrieval query for search: include recent_node_id if current query has none
        retrieval_query = query_str
        if not node_id_in_query and recent_node_id:
            retrieval_query = f"{recent_node_id} {query_str}"

        base_retriever = self.retriever.get_retriever(filters)
        if retrieval_query != query_str:
            target_retriever = base_retriever
            class ContextualWrapperRetriever(BaseRetriever):
                def _retrieve(self, query_bundle: QueryBundle, **kwargs):
                    if hasattr(target_retriever, "_retrieve"):
                        return target_retriever._retrieve(QueryBundle(query_str=retrieval_query), **kwargs)
                    return target_retriever.retrieve(retrieval_query)
                def retrieve(self, str_or_bundle, **kwargs):
                    if hasattr(target_retriever, "retrieve"):
                        return target_retriever.retrieve(retrieval_query)
                    return self._retrieve(QueryBundle(query_str=retrieval_query), **kwargs)
            engine_retriever = ContextualWrapperRetriever()
        else:
            engine_retriever = base_retriever

        # Add strict unknown-alarm/no-answer behavior
        target_sop_file = None
        if alarm_code:
            # Retrieve nodes to verify if the alarm code is present in context
            try:
                retrieved_nodes = engine_retriever.retrieve(retrieval_query)
                has_alarm = False
                for node_with_score in retrieved_nodes:
                    node_text = node_with_score.node.get_content().upper()
                    meta = node_with_score.node.metadata
                    
                    if str(meta.get("alarm_code", "")) == str(alarm_code):
                        has_alarm = True
                        target_sop_file = meta.get("file_name")
                        break
                        
                    # Check text as fallback
                    if (f"ALARM_{alarm_code}" in node_text or 
                        f"ALARM_CODE_{alarm_code}" in node_text or
                        f"ALARM {alarm_code}" in node_text or
                        f"ALARM CODE {alarm_code}" in node_text or
                        f"_{alarm_code}_" in node_text or
                        f" {alarm_code} " in node_text):
                        has_alarm = True
                        target_sop_file = meta.get("file_name")
                        break
                        
                if not has_alarm:
                    return _OutOfScopeResponse("I cannot find the procedure for this in the provided Methods of Procedure.")
                
                # Avoid redundant second retrieval: reuse pre-retrieved nodes for synthesis
                exact_nodes = [n for n in retrieved_nodes if n.node.metadata.get("file_name") == target_sop_file] if target_sop_file else retrieved_nodes
                if exact_nodes:
                    class ExactSOPRetriever(BaseRetriever):
                        def __init__(self, nodes):
                            super().__init__()
                            self.nodes = nodes
                        def _retrieve(self, query_bundle: QueryBundle, **kwargs):
                            return self.nodes
                        def retrieve(self, str_or_bundle, **kwargs):
                            return self.nodes
                    engine_retriever = ExactSOPRetriever(exact_nodes)
            except Exception as e:
                # If retrieval fails here, let the chat engine try or fallback normally
                pass

        # Use active session memory when available, preventing global singleton race conditions
        memory = active_memory or ChatMemoryBuffer.from_defaults(
            token_limit=self.token_limit
        )

        from llama_index.core.prompts import PromptTemplate
        custom_refine_template = PromptTemplate(
            "Review the existing answer and the new context below.\n"
            "CRITICAL: If the new context is about a different alarm code or unrelated entity, "
            "DO NOT erase or contradict the existing answer. Just output the existing answer unchanged.\n"
            "--------------------\n"
            "{context_msg}\n"
            "--------------------\n"
            "Existing Answer:\n"
            "{existing_answer}\n"
            "--------------------\n"
            "Final Answer: "
        )

        chat_engine = ContextChatEngine.from_defaults(
            retriever=engine_retriever,
            llm=self.llm,
            memory=memory,
            system_prompt=full_system_prompt,
            context_refine_template=custom_refine_template,
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

        # Add strict unknown-alarm/no-answer behavior for stateless queries as well
        alarm_match = re.search(r'\bALARM(?:[_\s-]*(?:CODE)?[_\s-]*)?(\d+)\b', query_str, re.IGNORECASE)
        alarm_code = None
        if alarm_match:
            alarm_code = alarm_match.group(1)
        elif query_str.strip().isdigit() and 3 <= len(query_str.strip()) <= 5:
            alarm_code = query_str.strip()

        if alarm_code:
            try:
                retrieved_nodes = base_retriever.retrieve(query_str)
                has_alarm = False
                target_sop_file = None
                for node_with_score in retrieved_nodes:
                    node_text = node_with_score.node.get_content().upper()
                    meta = node_with_score.node.metadata
                    if str(meta.get("alarm_code", "")) == str(alarm_code):
                        has_alarm = True
                        target_sop_file = meta.get("file_name")
                        break
                    if (f"ALARM_{alarm_code}" in node_text or 
                        f"ALARM_CODE_{alarm_code}" in node_text or
                        f"ALARM {alarm_code}" in node_text or
                        f"ALARM CODE {alarm_code}" in node_text or
                        f"_{alarm_code}_" in node_text or
                        f" {alarm_code} " in node_text):
                        has_alarm = True
                        target_sop_file = meta.get("file_name")
                        break
                if not has_alarm:
                    return _OutOfScopeResponse("I cannot find the procedure for this in the provided Methods of Procedure.")

                if target_sop_file:
                    exact_nodes = [n for n in retrieved_nodes if n.node.metadata.get("file_name") == target_sop_file]
                    if exact_nodes:
                        class ExactSOPStatelessRetriever(BaseRetriever):
                            def __init__(self, nodes):
                                super().__init__()
                                self.nodes = nodes
                            def _retrieve(self, query_bundle: QueryBundle, **kwargs):
                                return self.nodes
                            def retrieve(self, str_or_bundle, **kwargs):
                                return self.nodes
                        base_retriever = ExactSOPStatelessRetriever(exact_nodes)
            except Exception:
                pass

        engine = RetrieverQueryEngine.from_args(
            retriever=base_retriever,
            llm=self.llm,
            text_qa_template=dynamic_prompt,
            response_mode=ResponseMode.TREE_SUMMARIZE
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
