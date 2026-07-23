<div align="center">
  <h1>🌐 NetRestore: Agentic RAG for Telecom Network Recovery</h1>
  <p><i>An advanced Hybrid-Search AI System designed to instantly diagnose and provide Standard Operating Procedures (SOPs) for critical telecommunications equipment failures.</i></p>
  <br>
  <h3>🔴 <a href="https://netrestore.streamlit.app/">Live Demo Available Here</a></h3>
</div>

---

## 🚀 Overview

In enterprise telecommunications, when a core router (e.g., Nokia, Cisco, Juniper) experiences an alarm, network engineers spend critical minutes digging through thousands of pages of PDF manuals to find the correct recovery procedure. 

**NetRestore** solves this by using a highly optimized, Agentic Retrieval-Augmented Generation (RAG) architecture. It allows engineers to query a specific network node and receive instantaneous, hallucination-free, step-by-step recovery procedures based *only* on the manufacturer's exact SOPs.

---

## 🧠 Core AI Architecture

This is not a basic LangChain wrapper. NetRestore is built on a highly customized LlamaIndex backend designed for exact-match retrieval in high-stakes environments.

### 1. Hybrid Search with Reciprocal Rank Fusion (RRF)
Dense vector search (Cosine Similarity) often fails on exact alphanumeric matches (e.g., differentiating between `ALARM_4401` and `ALARM_4402`). NetRestore solves this by executing a dual-pipeline search:
*   **Sparse Retrieval (BM25):** For exact keyword and alarm code matching.
*   **Dense Retrieval (SentenceTransformers):** For semantic meaning and context.
*   **Fusion:** Both result sets are mathematically fused using Reciprocal Rank Fusion (RRF) to guarantee the highest accuracy retrieval.

### 2. $O(1)$ Hard Metadata Filtering
Searching a global database for a specific router's SOP introduces latency and hallucination risks. 
During data ingestion, custom Regex pipelines extract the exact `Node ID` from the PDF texts and inject it into the ChromaDB metadata. When a user selects a Node in the UI, the system applies a hard `Where` filter to the database, instantly restricting the search space to only the relevant documents.

### 3. Agentic Graph Context Injection
Network failures are rarely isolated; they cascade. 
Before the LLM generates an answer, the Python backend reads a dynamic `network_topology.json` graph, traverses the edges to find connected child routers, calculates the downstream "blast radius" of the failure, and injects this graph context directly into the LLM prompt. 

---

## 🏗️ Data Engineering Pipeline

To simulate a real-world enterprise environment, this project features a massive synthetic data generation pipeline:
*   **LLM Data Generation:** Uses the Groq API (Llama-3) to synthetically generate **675 heavily-structured, domain-specific Telecom SOP PDFs** spanning Cisco, Juniper, Nokia, Ericsson, Huawei, and Arista equipment.
*   **Automated Ingestion:** A local automated pipeline that parses the PDFs, chunks the data, calculates embeddings, and indexes them into a local **ChromaDB (SQLite)** vector database.

---

## 💻 Tech Stack

*   **AI Framework:** LlamaIndex
*   **Vector Database:** ChromaDB
*   **Embeddings:** HuggingFace (`all-MiniLM-L6-v2`)
*   **LLM Provider:** Groq API (Llama-3-8b)
*   **Hybrid Search:** BM25 Sparse + Dense Vector
*   **Frontend:** Streamlit
*   **DevOps:** Docker Compose, Jenkins

---



## 🐳 Docker Deployment

To deploy this in a production-like containerized environment, simply use Docker Compose:
```bash
docker-compose up -d --build
```
The app will be available at `http://localhost:8501`.

---

## 📊 Evaluation & Testing
The system utilizes a dual-evaluation strategy:
1.  **Fast CI/CD Testing:** A custom Python script (`src/evaluation/evaluate.py`) that checks Mean Reciprocal Rank (MRR) and exact Keyword Hit Rates for automated testing pipelines.
2.  **Deep NLP Evaluation:** A Jupyter Notebook (`notebooks/evaluation_ragas.ipynb`) leveraging the **RAGAS framework** to mathematically score the LLM on Faithfulness and Answer Relevance.
