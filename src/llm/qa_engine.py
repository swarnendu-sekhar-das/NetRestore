from llama_index.core.chat_engine import ContextChatEngine
from llama_index.core.memory import ChatMemoryBuffer
from llama_index.core.query_engine import RetrieverQueryEngine
from src.llm.generator import get_llm_generator
from src.llm.prompts import SYSTEM_PROMPT, procedural_qa_prompt, legacy_procedural_qa_prompt

class ProceduralQAEngine:
    """
    Ties together the Vector Retriever, Chat Memory, and the LLM
    into a cohesive conversational QA pipeline with chain-of-thought reasoning.
    
    Supports two modes:
    - Conversational (default): Uses ContextChatEngine with ChatMemoryBuffer for
      multi-turn chat with CoT reasoning. Follow-up questions are contextual.
    - Legacy/stateless: Falls back to RetrieverQueryEngine for single-shot QA
      (used by test scripts).
    """
    
    def __init__(self, retriever_pipeline, token_limit: int = 3072):
        """
        Expects an instance of TelecomHybridRetriever from Phase 3.
        
        Args:
            retriever_pipeline: TelecomHybridRetriever instance
            token_limit: Maximum tokens for the chat memory sliding window.
                         3072 is conservative for Llama-3.1-8B's 8K context window.
        """
        self.retriever = retriever_pipeline
        self.llm = get_llm_generator()
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
        Conversational query with chain-of-thought + persistent memory.

        The ContextChatEngine is reused across calls (stored as self._chat_engine)
        so that ChatMemoryBuffer genuinely accumulates all previous turns.
        It is only rebuilt when the filters change (new vendor/alarm selection).

        Returns a response object with .response (text) and .source_nodes (citations).
        """
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
                system_prompt=SYSTEM_PROMPT,
                context_template=(
                    "Here are the relevant SOP documents retrieved for this query:\n"
                    "---------------------\n"
                    "{context_str}\n"
                    "---------------------\n"
                ),
            )

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
