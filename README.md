<div align="center">
  <h1>NetRestore: Hybrid RAG for Telecom SOP Retrieval</h1>
  <p><i>A hybrid-search assistant for finding and presenting Standard Operating Procedures (SOPs) for telecommunications equipment failures.</i></p>
  <br>
  <h3><a href="https://netrestore.streamlit.app/">Live Demo Available Here</a></h3>
</div>

---

## Overview

In enterprise telecommunications, when a core router (e.g., Nokia, Cisco, Juniper) experiences an alarm, network engineers spend critical minutes digging through thousands of pages of PDF manuals to find the correct recovery procedure. 

**NetRestore** helps engineers locate relevant SOPs from a local synthetic telecom corpus. It retrieves supporting chunks and asks an LLM to present a step-by-step response grounded in that context. Retrieval and prompting reduce unsupported answers, but they do not guarantee correctness; an authorised operator must review any operational procedure.

---

## Core AI Architecture

This is not a basic LangChain wrapper. NetRestore is built on a highly customized LlamaIndex backend designed for exact-match retrieval in high-stakes environments.

### 1. Hybrid Search with Reciprocal Rank Fusion (RRF)
Dense vector search (Cosine Similarity) often fails on exact alphanumeric matches (e.g., differentiating between `ALARM_4401` and `ALARM_4402`). NetRestore solves this by executing a dual-pipeline search:
*   **Sparse Retrieval (BM25):** For exact keyword and alarm code matching.
*   **Dense Retrieval (SentenceTransformers):** For semantic meaning and context.
*   **Fusion:** Both result sets are mathematically fused using Reciprocal Rank Fusion (RRF), combining lexical and semantic rank evidence before reranking.

### 2. Exact Metadata Filtering
During data ingestion, custom Regex pipelines extract an exact `Node ID` from PDF text and inject it into ChromaDB metadata. When a user selects a Node in the UI, the vector retriever passes an exact metadata filter to ChromaDB and the BM25 path applies the same filter after scoring its in-memory corpus. This improves precision, but filtering cost is backend- and corpus-dependent; it is not claimed to be $O(1)$.

### 3. Bounded Static Topology Reachability Context
Network failures are rarely isolated. For an exact node ID, the backend reads the static `network_topology.json` adjacency list and performs a bounded breadth-first traversal (two hops by default). It injects direct and indirect reachable nodes, paths, and unresolved references into the LLM prompt. This is advisory topology context, not confirmed live outage impact or telemetry-based blast-radius calculation.

---

## Data Engineering Pipeline

To simulate a real-world enterprise environment, this project features a massive synthetic data generation pipeline:
*   **LLM Data Generation:** Uses the Groq API (Llama-3) to synthetically generate **675 heavily-structured, domain-specific Telecom SOP PDFs** spanning Cisco, Juniper, Nokia, Ericsson, Huawei, and Arista equipment.
*   **Automated Ingestion:** A local automated pipeline that parses only the PDFs under `data/sops/`, chunks the data, calculates embeddings, and indexes them into a local **ChromaDB (SQLite)** vector database.

---

## Tech Stack

*   **AI Framework:** LlamaIndex
*   **Vector Database:** ChromaDB
*   **Embeddings:** HuggingFace (`all-MiniLM-L6-v2`)
*   **LLM Provider:** Groq API (Llama-3-8b)
*   **Hybrid Search:** BM25 Sparse + Dense Vector
*   **Frontend:** Streamlit
*   **DevOps:** Docker Compose, Jenkins

---



## Docker Deployment

To deploy this in a production-like containerized environment, simply use Docker Compose:
```bash
docker-compose up -d --build
```
The app will be available at `http://localhost:8501`.

---

## Evaluation & Testing
The system utilizes a dual-evaluation strategy:
1.  **Fast CI/CD Testing:** A custom Python script (`src/evaluation/evaluate.py`) with 25 file-grounded cases. It reports Exact Document Hit@1, Exact Document Recall@3, and MRR based on the first retrieval of the expected SOP file. Keyword hit rate is retained only as a secondary context proxy.
2.  **Deep NLP Evaluation:** A Jupyter Notebook (`notebooks/evaluation_ragas.ipynb`) leveraging the **RAGAS framework** to mathematically score the LLM on Faithfulness and Answer Relevance.

The included benchmark is a regression dataset for this synthetic corpus, not a claim of production accuracy. LLM generation evaluation remains optional and requires a configured Groq API key.
