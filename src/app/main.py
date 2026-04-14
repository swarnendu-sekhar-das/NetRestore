import streamlit as st
import os
import sys
import logging
import time
import json

# Ensure the src module is in the path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from src.retrieval.vector_store import TelecomVectorStore
from src.retrieval.hybrid_search import TelecomHybridRetriever
from src.llm.qa_engine import ProceduralQAEngine
from llama_index.core.memory import ChatMemoryBuffer

# ---------------------------------------------------------------------------
# Structured JSON Logging (for ELK Stack ingestion via Filebeat/Logstash)
# ---------------------------------------------------------------------------
logger = logging.getLogger("telecom_rag")
if not logger.handlers:
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(
        '{"timestamp":"%(asctime)s","level":"%(levelname)s","module":"%(name)s","message":%(message)s}'
    ))
    logger.addHandler(handler)

# Configure the Streamlit page
st.set_page_config(
    page_title="Telecom QA RAG",
    page_icon="📡",
    layout="wide",
)

# Initialize the QA Engine once and store it in session state
@st.cache_resource
def load_qa_engine(api_key: str = None):
    db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "chroma_db"))
    if not os.path.exists(db_path):
        return None
    
    # We must set the Env variable here immediately so LlamaIndex picks it up during initialization
    if api_key:
        os.environ["GROQ_API_KEY"] = api_key
        
    vs_manager = TelecomVectorStore(db_path=db_path)
    retriever = TelecomHybridRetriever(vector_store_manager=vs_manager, similarity_top_k=2)
    return ProceduralQAEngine(retriever_pipeline=retriever)

# Header Information
st.markdown("""
<h1 style='text-align: center;'>
    <span style='font-size: 60px;'>📡</span> 
</h1>
""", unsafe_allow_html=True)
st.markdown("""
<h1 style='text-align: center; font-size: 45px;'>
    Procedural QA RAG for Telecom Service Restoration
</h1>
""", unsafe_allow_html=True)
st.markdown("""
<p style='text-align: center; font-size: 18px;'>
A RAG-based system designed for telecom network restoration operations by retrieving precise restoration SOPs for outages, faults, and incidents using hybrid search and LLM reasoning, enabling faster and more reliable service recovery.
</p>
""", unsafe_allow_html=True)


if "GROQ_API_KEY" not in os.environ and "api_key" not in st.session_state:
    # Sidebar input for API Key if not found in env
    api_key = st.sidebar.text_input("Groq API Key (Free)", type="password")
    if not api_key:
        st.warning("Please enter your Groq API Key (from console.groq.com) in the sidebar to use the free LLM.")
        st.stop()
    else:
        st.session_state.api_key = api_key
        os.environ["GROQ_API_KEY"] = api_key

# Load Engine dynamically AFTER key is set
qa_engine = load_qa_engine(st.session_state.get("api_key", os.environ.get("GROQ_API_KEY")))

if not qa_engine:
    st.error("Vector Database not found! Please run the Phase 2/3 test scripts first to index the documents.")
    st.stop()

# ---------------------------------------------------------------------------
# Initialize Chat Memory (persists across Streamlit re-runs within a session)
# ---------------------------------------------------------------------------
if "chat_memory" not in st.session_state:
    st.session_state.chat_memory = ChatMemoryBuffer.from_defaults(token_limit=3072)

# Inject session-specific memory into the engine for conversational continuity
qa_engine.set_memory(st.session_state.chat_memory)

st.divider()

# Sidebar for explicit Metadata Filtering (Mimicking Hybrid Keyword Search)
st.sidebar.header("Pre-Filtering (Hybrid Search)")
st.sidebar.markdown("Use these filters to ensure exact error codes are retrieved via Metadata Filtering, solving the issue of pure vector search missing specific model numbers.")
vendor_filter = st.sidebar.selectbox(
    "Equipment Vendor", 
    ["Any", "Nokia", "Cisco", "Juniper", "Ericsson", "Huawei"]
)
VENDOR_ALARM_HINTS = {
    "Cisco":    "Cisco codes: 301–302, 1000–1099",
    "Nokia":    "Nokia codes: 404, 501, 1100–1199",
    "Ericsson": "Ericsson codes: 701–702, 1300–1399",
    "Juniper":  "Juniper codes: 601–602, 1200–1299",
    "Huawei":   "Huawei codes: 801–802, 1400–1499",
    "Any":      "e.g. 301, 404, 601, 701, 801, 1000",
}
alarm_hint = VENDOR_ALARM_HINTS.get(vendor_filter, "e.g. 1000, 1101, 1201")
alarm_filter = st.sidebar.text_input(f"Exact Alarm Code ({alarm_hint})", value="")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Add a clear chat button to the sidebar
if st.sidebar.button("Clear Chat History", use_container_width=True):
    st.session_state.messages = []
    st.session_state.chat_memory = ChatMemoryBuffer.from_defaults(token_limit=3072)
    qa_engine.set_memory(st.session_state.chat_memory)
    logger.info(json.dumps({"event": "chat_cleared"}))
    st.rerun()

# Display chat history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if "sources" in message and message["sources"]:
            with st.expander("Show Retrieved Context (For Academic Evaluation)"):
                for source in message["sources"]:
                    st.markdown(f"**Document:** `{source['file_name']}`  \n**Section Header:** `{source['header']}`  \n**Confidence Score:** `{source['score']:.2f}`")
                    st.text(source['text'])

# React to user input
if prompt := st.chat_input("Ask a procedural question (e.g., 'How to clear ALARM_CODE_404 on router XYZ?'): "):
    # Display user message in chat message container
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Prepare filters
    filters = {}
    if vendor_filter != "Any":
        filters["equipment_vendor"] = vendor_filter
    if alarm_filter.strip():
        filters["alarm_code"] = alarm_filter.strip()
        
    # Query Engine with timing for structured logging
    with st.chat_message("assistant"):
        with st.spinner("Retrieving SOPs and Synthesizing Answer (with Chain-of-Thought)..."):
            try:
                start_time = time.time()
                response = qa_engine.query(prompt, filters=filters if filters else None)
                latency = time.time() - start_time
                
                # Get response text (ContextChatEngine returns AgentChatResponse)
                response_text = str(response)
                
                # --- Zero-results guard ---
                num_sources = len(response.source_nodes) if hasattr(response, 'source_nodes') and response.source_nodes else 0
                if num_sources == 0 or not response_text.strip():
                    parts = []
                    if alarm_filter.strip():
                        parts.append(f"alarm code **{alarm_filter.strip()}**")
                    if vendor_filter != "Any":
                        parts.append(f"vendor **{vendor_filter}**")
                    detail = " for " + " and ".join(parts) if parts else ""
                    response_text = (
                        f"⚠️ No matching SOP documents found{detail}.\n\n"
                        f"**Possible reasons:**\n"
                        f"- The alarm code may not exist in the {vendor_filter} dataset\n"
                        f"- Try a 4-digit code (e.g. `1101`, `1201`, `1301`) instead\n"
                        f"- Clear the alarm code filter and search by description only"
                    )
                
                st.markdown(response_text)
                
                # Structured logging for ELK ingestion
                logger.info(json.dumps({
                    "event": "query_executed",
                    "query": prompt,
                    "vendor_filter": vendor_filter,
                    "alarm_filter": alarm_filter,
                    "latency_seconds": round(latency, 3),
                    "num_sources": len(response.source_nodes) if hasattr(response, 'source_nodes') and response.source_nodes else 0,
                    "status": "success"
                }))
                
                # Extract Sources explicitly for grading
                source_data = []
                if hasattr(response, 'source_nodes') and response.source_nodes:
                    with st.expander("Show Retrieved Context (For Academic Evaluation)"):
                        for node in response.source_nodes:
                            file_name = node.node.metadata.get('file_name', 'Unknown')
                            header = node.node.metadata.get('header_path', 'No Header')
                            source_text = node.node.get_content()
                            score = node.score if node.score is not None else 0.0
                            
                            st.markdown(f"**Document:** `{file_name}`  \n**Section Header:** `{header}`  \n**Confidence Score:** `{score:.2f}`")
                            st.text(source_text[:500] + "...\n[TRUNCATED]")
                            
                            source_data.append({
                                "file_name": file_name,
                                "header": header,
                                "score": score,
                                "text": source_text[:500] + "...\n[TRUNCATED]"
                            })
                            
                # Add assistant response to chat history
                st.session_state.messages.append({"role": "assistant", "content": response_text, "sources": source_data})
                
            except Exception as e:
                latency = time.time() - start_time
                error_msg = f"**Error:** Failed to generate response. Please check your Groq API Key.\n\n`{str(e)}`"
                st.error(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})
                
                # Log the error for ELK
                logger.error(json.dumps({
                    "event": "query_failed",
                    "query": prompt,
                    "vendor_filter": vendor_filter,
                    "alarm_filter": alarm_filter,
                    "latency_seconds": round(latency, 3),
                    "error": str(e),
                    "status": "error"
                }))
