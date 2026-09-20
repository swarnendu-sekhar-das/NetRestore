import streamlit as st
import os
import time
import requests
import uuid
import json

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# We expect BACKEND_URL to be passed in, otherwise default to localhost:8000
BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8000")

# Configure the Streamlit page.
st.set_page_config(
    page_title="NetRestore",
    page_icon="📡",
    layout="wide",
)

# Generate a unique session ID for chat memory
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

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
        border-right: 1px solid #e2e8f0;
    }
    
    .sidebar-title {
        color: #1e293b;
        font-weight: 600;
        margin-bottom: 1rem;
    }
    
    /* Chat messages */
    .stChatMessage {
        background-color: #f8f9fa;
        color: #1e293b;
        border-radius: 8px;
        padding: 1rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        margin-bottom: 1rem;
        border: 1px solid #e2e8f0;
    }

    /* Streamlit's dark theme otherwise keeps its light text inside our
       deliberately white chat cards, making responses unreadable. */
    .stChatMessage [data-testid="stMarkdownContainer"],
    .stChatMessage [data-testid="stMarkdownContainer"] > p,
    .stChatMessage [data-testid="stMarkdownContainer"] > ul,
    .stChatMessage [data-testid="stMarkdownContainer"] > ol,
    .stChatMessage [data-testid="stMarkdownContainer"] > h1,
    .stChatMessage [data-testid="stMarkdownContainer"] > h2,
    .stChatMessage [data-testid="stMarkdownContainer"] > h3,
    .stChatMessage [data-testid="stText"] {
        color: #1e293b !important;
    }

    /* We removed the aggressive wildcard (*) above because it was overriding code block text colors. 
       Now we specifically target code blocks with high specificity to ensure light text on dark background. */
    .stChatMessage [data-testid="stMarkdownContainer"] pre,
    .stChatMessage [data-testid="stMarkdownContainer"] pre *,
    .stChatMessage [data-testid="stMarkdownContainer"] code {
        color: #f8f9fa !important;
    }

    .stChatMessage [data-testid="stMarkdownContainer"] pre {
        background-color: #1e293b !important;
        border: 1px solid #334155 !important;
        border-radius: 6px;
        padding: 0.75rem;
    }

    /* Inline code blocks (not inside pre) */
    .stChatMessage [data-testid="stMarkdownContainer"] p code,
    .stChatMessage [data-testid="stMarkdownContainer"] li code {
        color: #e11d48 !important;
        background-color: #f1f5f9 !important;
        padding: 0.1rem 0.3rem;
        border-radius: 4px;
    }

    /* Source snippets outside chat */
    pre {
        background-color: #1e293b;
        color: #f8f9fa;
        border: 1px solid #334155;
        border-radius: 6px;
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
</style>
""", unsafe_allow_html=True)

# Display the page header.
st.markdown("""
<div class="header-container">
    <div class="header-icon">📡</div>
    <h1 class="header-title">NetRestore: Procedural QA RAG for Network Fault Restoration</h1>
    <p class="header-subtitle">
        A RAG-based system designed for network fault restoration operations.
    </p>
</div>
""", unsafe_allow_html=True)

st.divider()

# Show configuration in the sidebar.
st.sidebar.markdown('<h2 class="sidebar-title">⚙️ Configuration</h2>', unsafe_allow_html=True)

# Backend Status Check
st.sidebar.markdown('<h3 class="sidebar-title">🔌 API Status</h3>', unsafe_allow_html=True)
try:
    health_resp = requests.get(f"{BACKEND_URL}/health", timeout=3)
    if health_resp.status_code == 200:
        st.sidebar.success(f"Backend API: Connected")
    else:
        st.sidebar.warning(f"Backend API: Degraded")
except Exception as e:
    st.sidebar.error(f"Backend API: Disconnected")
    st.error(f"Cannot reach Backend API at {BACKEND_URL}. Please ensure it is running.")

st.sidebar.markdown("---")
st.sidebar.markdown('<h3 class="sidebar-title">📋 Syslog / Telemetry Input</h3>', unsafe_allow_html=True)
st.sidebar.markdown("Paste raw device syslogs, alerts, or telemetry here for automated analysis.")

syslog_input = st.sidebar.text_area("Raw Syslog Payload:", height=150, key="syslog_input")
analyze_syslog_clicked = st.sidebar.button("Analyze Telemetry", type="primary", use_container_width=True)

# Create the displayed chat history for a new session.
if "messages" not in st.session_state:
    st.session_state.messages = []

# Add a button to clear the current chat.
st.sidebar.markdown("---")
if st.sidebar.button("🗑️ Clear Chat History", use_container_width=True, type="secondary"):
    st.session_state.messages = []
    # Generate a new session ID so the backend uses a fresh memory buffer
    st.session_state.session_id = str(uuid.uuid4())
    st.rerun()

# Render earlier messages after Streamlit reruns the script.
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        if message.get("fallback"):
            st.warning("⚠️ AI Generation is currently unavailable. Displaying raw retrieved context.")
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

    # Run the query against the backend API
    with st.chat_message("assistant"):
        with st.spinner("Retrieving SOPs and Synthesizing Answer..."):
            try:
                payload = {
                    "question": prompt,
                    "session_id": st.session_state.session_id
                }
                
                response = requests.post(f"{BACKEND_URL}/ask", json=payload, timeout=60)
                
                if response.status_code == 200:
                    data = response.json()
                    answer_text = data.get("answer", "")
                    sources = data.get("sources", [])
                    fallback = data.get("fallback", False)
                    
                    if fallback:
                        st.warning("⚠️ AI Generation is currently unavailable. Displaying raw retrieved context.")
                        
                    st.markdown(answer_text)
                    
                    if sources:
                        with st.expander("📄 Show Retrieved Context", expanded=False):
                            for idx, source in enumerate(sources, 1):
                                st.markdown(f"### Source {idx}")
                                st.markdown(f"**Document:** `{source['file_name']}`  \n**Section Header:** `{source['header']}`  \n**Confidence Score:** `{source['score']:.2f}`")
                                st.text(source['text'][:500] + "...\n[TRUNCATED]")
                                if idx < len(sources):
                                    st.markdown("---")
                                    
                    st.session_state.messages.append({
                        "role": "assistant", 
                        "content": answer_text, 
                        "sources": sources,
                        "fallback": fallback
                    })
                else:
                    error_msg = f"**Error from API (Status {response.status_code}):**\n`{response.text}`"
                    st.error(error_msg)
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})
                    
            except requests.exceptions.RequestException as e:
                error_msg = f"**Connection Error:** Could not reach the API at {BACKEND_URL}.\n\n`{str(e)}`"
                st.error(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})
