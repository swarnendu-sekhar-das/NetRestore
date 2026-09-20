# NetRestore

## Overview
NetRestore is an advanced Retrieval-Augmented Generation (RAG)-based Procedural Question Answering System tailored for Network Fault Restoration. It assists network operators and engineers in rapidly diagnosing issues and executing precise restoration procedures across heterogeneous equipment from multiple vendors, including Nokia, Cisco, Juniper, Ericsson, and Huawei. By utilizing a conversational UI and an intelligent search system, NetRestore significantly reduces the time required to resolve network faults and adhere to Service Level Agreements (SLAs).

> **Note:** NetRestore is an **operator-assist only** tool and **does not execute network changes** autonomously. The SOPs, evaluation data, and network topology data used in this project are completely **synthetic** for demonstration purposes. The topology mapping is **static and advisory** only.

## Features
- **Hybrid Search Retrieval:** Combines Dense Vector Retrieval (semantic search using embeddings) and Sparse Keyword Retrieval (BM25 for exact alarm codes/identifiers) to ensure high-accuracy document fetching.
- **Cross-Encoder Reranking:** Uses an advanced cross-encoder model to rerank retrieved documents, maximizing contextual relevance.
- **Conversational QA with Chain-of-Thought (CoT):** Leverages Large Language Models to provide precise, step-by-step reasoning and actionable restoration steps.
- **Multi-Vendor Support:** Metadata-based filtering allows the system to accurately distinguish and query procedures specific to different equipment vendors.
- **Comprehensive DevOps & CI/CD Pipeline:** Fully containerized with Docker, featuring automated testing, building, and deployments via Jenkins, and orchestrated on Kubernetes.

## Tech Stack

### Core RAG & Backend
- **Frameworks:** [LlamaIndex](https://www.llamaindex.ai/), [FastAPI](https://fastapi.tiangolo.com/)
- **Programming Language:** Python 3.11
- **LLM Integration:** Groq SDK for high-speed inference
- **Embeddings:** HuggingFace (`all-MiniLM-L6-v2`)
- **Reranking:** Sentence Transformers (`ms-marco-MiniLM-L-6-v2`)
- **Retrieval:** BM25 (Sparse) + ChromaDB (Dense)
- **Routing:** Rule-based router for intent classification

### Data & Vector Store
- **Vector Database:** [ChromaDB](https://www.trychroma.com/)
- **Document Processing:** pypdf, reportlab (for synthetic SOP generation and parsing)
- **Testing & Evaluation:** Ragas (RAG metrics evaluation), Pytest

### Frontend
- **UI Framework:** [Streamlit](https://streamlit.io/)

### DevOps, Deployment & Monitoring
- **Containerization:** Docker, Docker Compose
- **Orchestration:** Kubernetes (K8s)
- **CI/CD:** Jenkins (Pipeline for linting, testing, Docker image building/pushing, and K8s rolling deployment)
- **Logging:** python-json-logger

## System Architecture
The application follows a modern, containerized microservices architecture:
1. **Frontend:** A Streamlit application providing an interactive, conversational user interface for network engineers.
2. **Backend:** A scalable FastAPI service that acts as the core engine, orchestrating the RAG pipeline (hybrid retrieval, cross-encoder reranking, and LLM synthesis).
3. **Storage:** ChromaDB running alongside the backend for managing document embeddings, while Persistent Volume Claims (PVCs) handle shared data storage.
4. **DevOps Pipeline:** Jenkins automatically polls for code changes, executes linting (`flake8`) and unit/integration tests (`pytest`, `ragas`), builds Docker images, pushes them to Docker Hub, and triggers a rolling update on the Kubernetes cluster.

## Setup and Deployment
Detailed deployment instructions are documented separately. Please refer to the **Netrestore Deployment Guide** for a comprehensive walkthrough on:
- Local startup using the backend script: `bash scripts/startup.sh`
- Local deployment using Docker Compose.
- Containerized MVP deployment on a Kubernetes cluster.
- Setting up and triggering the Jenkins CI/CD pipeline.
