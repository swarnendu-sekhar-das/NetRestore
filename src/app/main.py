import streamlit as st
import os
import sys
import logging
import time
import json
from pythonjsonlogger import jsonlogger

from dotenv import load_dotenv

# Load environment variables first
load_dotenv()

from src.retrieval.vector_store import TelecomVectorStore
from src.retrieval.hybrid_search import TelecomHybridRetriever
from src.llm.qa_engine import ProceduralQAEngine
from src.llm.router import SemanticRouter
from src.llm.topology import NetworkTopologyService
from src.llm.generator import get_llm_generator
from llama_index.core.memory import ChatMemoryBuffer

# Set up JSON logging for the app (ELK Stack Ready).
logger = logging.getLogger("netrestore")
if not logger.handlers:
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    formatter = jsonlogger.JsonFormatter('%(asctime)s %(levelname)s %(name)s %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

# Configure the Streamlit page.
st.set_page_config(
    page_title="NetRestore",
    page_icon="📡",
    layout="wide",
)

# Custom styles for the page.
st.markdown("""
<style>
    /* Page layout */
    .main {
        background-color: #f8f9fa;
    }
    
    /* Header */
    .header-container {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem 3rem;
        border-radius: 12px;
        margin-bottom: 2rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    .header-title {
        color: white;
        font-size: 2.5rem;
        font-weight: 700;
        text-align: center;
        margin: 0;
        text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.2);
    }
    
    .header-subtitle {
        color: rgba(255, 255, 255, 0.9);
        font-size: 1.1rem;
        text-align: center;
        margin-top: 1rem;
        line-height: 1.6;
    }
    
    .header-icon {
        font-size: 4rem;
        text-align: center;
        display: block;
        margin-bottom: 0.5rem;
    }
    
    /* Sidebar */
    .css-1d391kg {
        background-color: #ffffff;
    }
    
    .sidebar-title {
        color: #667eea;
        font-size: 1.3rem;
        font-weight: 600;
        margin-bottom: 1rem;
    }
    
    /* Chat messages */
    .stChatMessage {
        border-radius: 12px;
        margin-bottom: 1rem;
    }
    
    /* Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.5rem 1.5rem;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
    }
    
    /* Text inputs */
    .stTextInput > div > div > input {
        border-radius: 8px;
        border: 2px solid #e2e8f0;
        padding: 0.75rem;
        transition: border-color 0.3s ease;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #667eea;
        outline: none;
    }
    
    /* Select boxes */
    .stSelectbox > div > div > select {
        border-radius: 8px;
        border: 2px solid #e2e8f0;
        padding: 0.75rem;
    }
    
    /* Expanders */
    .streamlit-expanderHeader {
        background-color: #f1f5f9;
        border-radius: 8px;
        padding: 0.75rem;
        font-weight: 600;
        color: #475569;
    }
    
    /* Status messages */
    .stSuccess {
        background-color: #dcfce7;
        border-left: 4px solid #22c55e;
        padding: 1rem;
        border-radius: 8px;
    }
    
    .stError {
        background-color: #fee2e2;
        border-left: 4px solid #ef4444;
        padding: 1rem;
        border-radius: 8px;
    }
    
    .stWarning {
        background-color: #fef3c7;
        border-left: 4px solid #f59e0b;
        padding: 1rem;
        border-radius: 8px;
    }
    
    /* Information messages */
    .stInfo {
        background-color: #dbeafe;
        border-left: 4px solid #3b82f6;
        padding: 1rem;
        border-radius: 8px;
    }
    
    /* Footer */
    .footer {
        text-align: center;
        padding: 2rem;
        color: #64748b;
        font-size: 0.9rem;
        margin-top: 3rem;
        border-top: 1px solid #e2e8f0;
    }
</style>
""", unsafe_allow_html=True)

# Cache the stateless retrieval services.
@st.cache_resource
def load_retrieval_services():
    db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "chroma_db"))
    if not os.path.exists(db_path):
        return None, None, None
        
    vs_manager = TelecomVectorStore(db_path=db_path)
    from src.retrieval.hybrid_search import get_hybrid_retriever
    retriever = get_hybrid_retriever(vs_manager)
    router = SemanticRouter()
    topology_service = NetworkTopologyService()
    
    return retriever, router, topology_service

# Display the page header.
st.markdown("""
<div class="header-container">
    <div class="header-icon">📡</div>
    <h1 class="header-title">NetRestore: Procedural QA RAG for Network Fault Restoration</h1>
    <p class="header-subtitle">
        A RAG-based system designed for network fault restoration operations by retrieving precise restoration SOPs for outages, faults, and incidents using hybrid search and LLM reasoning, enabling faster and more reliable service recovery.
    </p>
</div>
""", unsafe_allow_html=True)


# Validate the Groq API key from the environment.
api_key = os.environ.get("GROQ_API_KEY")
if not api_key:
    st.error("Configuration Error: GROQ_API_KEY is not found in the environment.")
    st.info("Please open the `.env` file in the project root, add `GROQ_API_KEY=your_key_here`, and restart the app.")
    st.stop()

# Load shared read-only services.
retriever, router, topology_service = load_retrieval_services()

if not retriever:
    st.error("Vector Database not found! Please run the scripts first to index the documents.")
    st.stop()

# Create the stateful QA engine per-session.
if "qa_engine" not in st.session_state:
    llm = get_llm_generator(api_key=api_key)
    st.session_state.qa_engine = ProceduralQAEngine(
        retriever_pipeline=retriever,
        router=router,
        topology_service=topology_service,
        llm=llm
    )

qa_engine = st.session_state.qa_engine

# Create chat memory for a new session.
if "chat_memory" not in st.session_state:
    st.session_state.chat_memory = ChatMemoryBuffer.from_defaults(token_limit=3072)

# Give the engine the current session's chat memory.
qa_engine.set_memory(st.session_state.chat_memory)

st.divider()

# Show configuration in the sidebar.
st.sidebar.markdown('<h2 class="sidebar-title">⚙️ Configuration</h2>', unsafe_allow_html=True)
st.sidebar.markdown("---")
st.sidebar.markdown('<h3 class="sidebar-title">📋 Syslog / Telemetry Input</h3>', unsafe_allow_html=True)
st.sidebar.markdown("Paste raw device syslogs, alerts, or telemetry here for automated analysis. NetRestore will automatically extract IPs, assess blast radius, and retrieve the correct SOP.")

syslog_input = st.sidebar.text_area("Raw Syslog Payload:", height=150, key="syslog_input")
analyze_syslog_clicked = st.sidebar.button("Analyze Telemetry", type="primary", use_container_width=True)

# Create the displayed chat history for a new session.
if "messages" not in st.session_state:
    st.session_state.messages = []

# Add a button to clear the current chat.
st.sidebar.markdown("---")
if st.sidebar.button("🗑️ Clear Chat History", use_container_width=True, type="secondary"):
    st.session_state.messages = []
    st.session_state.chat_memory = ChatMemoryBuffer.from_defaults(token_limit=3072)
    qa_engine.set_memory(st.session_state.chat_memory)
    logger.info(json.dumps({"event": "chat_cleared"}))
    st.rerun()

# Render earlier messages after Streamlit reruns the script.
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if "sources" in message and message["sources"]:
            with st.expander("📄 Show Retrieved Context", expanded=False):
                for idx, source in enumerate(message["sources"], 1):
                    st.markdown(f"### Source {idx}")
                    st.markdown(f"**Document:** `{source['file_name']}`  \n**Section Header:** `{source['header']}`  \n**Confidence Score:** `{source['score']:.2f}`")
                    st.text(source['text'])
                    if idx < len(message["sources"]):
                        st.markdown("---")

# Handle user input from either chat or the syslog text area
prompt = st.chat_input("Ask a procedural question (e.g., 'How to clear ALARM_CODE_404 on router XYZ?'): ")
if analyze_syslog_clicked and st.session_state.syslog_input.strip():
    prompt = st.session_state.syslog_input.strip()

if prompt:
    # Show the user message first.
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Run the query and record its latency.
    with st.chat_message("assistant"):
        with st.spinner("Retrieving SOPs and Synthesizing Answer (with Chain-of-Thought)..."):
            try:
                start_time = time.time()
                # Query no longer needs exact-match metadata filters because BM25 sparse retrieval handles this accurately.
                response = qa_engine.query(prompt, filters=None)
                latency = time.time() - start_time
                
                # Convert the LlamaIndex response to display text.
                response_text = str(response)
                
                # Require sources for the first question in a chat.
                is_follow_up = len(st.session_state.messages) > 1
                num_sources = len(response.source_nodes) if hasattr(response, 'source_nodes') and response.source_nodes else 0
                
                if (num_sources == 0 and not is_follow_up) or not response_text.strip():
                    st.error("No documents found matching your query. Please try rephrasing.")
                    response_text = (
                        f"⚠️ No matching SOP documents found.\n\n"
                        f"**Possible reasons:**\n"
                        f"- The alarm code or query keywords may not exist in the dataset\n"
                        f"- Try searching with a raw syslog chunk"
                    )
                
                st.markdown(response_text)
                
                # Record the request outcome in the application log.
                logger.info(json.dumps({
                    "event": "query_executed",
                    "query": prompt,
                    "latency_seconds": round(latency, 3),
                    "num_sources": len(response.source_nodes) if hasattr(response, 'source_nodes') and response.source_nodes else 0,
                    "status": "success"
                }))
                
                # Store source snippets with the displayed answer.
                source_data = []
                if hasattr(response, 'source_nodes') and response.source_nodes:
                    with st.expander("📄 Show Retrieved Context", expanded=False):
                        for idx, node in enumerate(response.source_nodes, 1):
                            file_name = node.node.metadata.get('file_name', 'Unknown')
                            header = node.node.metadata.get('header_path', 'No Header')
                            source_text = node.node.get_content()
                            score = node.score if node.score is not None else 0.0
                            
                            st.markdown(f"### Source {idx}")
                            st.markdown(f"**Document:** `{file_name}`  \n**Section Header:** `{header}`  \n**Confidence Score:** `{score:.2f}`")
                            st.text(source_text[:500] + "...\n[TRUNCATED]")
                            if idx < len(response.source_nodes):
                                st.markdown("---")
                            
                            source_data.append({
                                "file_name": file_name,
                                "header": header,
                                "score": score,
                                "text": source_text[:500] + "...\n[TRUNCATED]"
                            })
                            
                # Save the assistant response in the current session.
                st.session_state.messages.append({"role": "assistant", "content": response_text, "sources": source_data})
                
            # Catching generic Exception here because the LLM API might throw various unpredictable errors (e.g., timeout, connection dropped, parsing failures)
            except Exception as e:
                latency = time.time() - start_time
                error_msg = f"**Error:** Failed to generate response. Please check your Groq API Key.\n\n`{str(e)}`"
                st.error(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})
                
                # Record the failure in the application log.
                logger.error(json.dumps({
                    "event": "query_failed",
                    "query": prompt,
                    "latency_seconds": round(latency, 3),
                    "error": str(e),
                    "status": "error"
                }))
