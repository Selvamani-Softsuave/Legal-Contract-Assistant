# 📁 Enterprise Legal Contract RAG — Project Folder Structure & Architecture Guide

This document provides a comprehensive, file-by-file and folder-by-folder breakdown of the **Enterprise Legal Contract RAG & Assistant Platform**. It explains **why each folder exists**, **what kind of files it contains**, and **how the components collaborate** within our clean, distributed architecture.

---

## 🧭 High-Level Architecture Pattern

The codebase is organized following **Hexagonal Architecture (Clean Architecture / Ports & Adapters)** and **Domain-Driven Design (DDD)**, decoupled across three primary runtimes:

```
┌────────────────────────────────────────────────────────────────────────┐
│                        frontend/ (Angular 19 SPA)                     │
│               User Interface, Document Management, Grounded Chat       │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ HTTP (Port 4201 / Nginx)
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                         backend/ (FastAPI Core)                        │
│   ┌────────────────────────────────────────────────────────────────┐   │
│   │ presentation / api   (Controllers & Routers)                   │   │
│   ├────────────────────────────────────────────────────────────────┤   │
│   │ application          (Business Use Cases & Orchestration)      │   │
│   ├────────────────────────────────────────────────────────────────┤   │
│   │ domain               (Pure Entities, Value Objects, Contracts) │   │
│   ├────────────────────────────────────────────────────────────────┤   │
│   │ infrastructure       (Database, Vector DB, Azure Adapters)     │   │
│   └────────────────────────────────────────────────────────────────┘   │
└───────────────┬───────────────────────────────────────┬────────────────┘
                │ Azure Queue                           │ SQL / HTTP
                ▼                                       ▼
┌───────────────────────────────────┐   ┌────────────────────────────────┐
│   processor/ (Azure Functions)    │   │  Databases & External Storage   │
│ Text Extraction, Legal Chunking,  │   │  - SQL Server 2022 (Port 1433) │
│ & ChromaDB Vector Synchronization │   │  - ChromaDB Vector (Port 8000) │
└───────────────────────────────────┘   │  - Azurite Storage (Port 10000)│
                                        └────────────────────────────────┘
```

---

## 🌳 Complete Directory Tree

```
legal-contract-rag/
├── .env.example                     # Sanitized environment template (no secrets)
├── Dockerfile                       # Multi-stage Python 3.11 container definition
├── docker-compose.yml               # Multi-container orchestrator (7 services)
├── README.md                        # Primary developer onboarding and quickstart guide
├── architecture.md                  # Executive architectural summary
├── run_capstone.py                  # End-to-end evaluation & verification script
│
├── backend/                         # FastAPI Application & AI Core
│   ├── Dockerfile                   # Backend production Dockerfile with ODBC drivers
│   ├── requirements.txt             # Backend Python dependencies
│   ├── alembic/                     # Relational database migration scripts
│   ├── scripts/                     # Startup and lifecycle scripts (start.sh)
│   └── app/                         # Core Python application package
│       ├── main.py                  # FastAPI application entry point
│       ├── api/v1/                  # REST API endpoints & route handlers
│       ├── application/             # Business logic use cases (Clean Architecture)
│       ├── domain/                  # Pure domain entities, value objects & ports
│       ├── infrastructure/          # Adapters (SQLAlchemy, Azurite, ChromaDB)
│       ├── presentation/            # Dependency injection & presentation helpers
│       ├── core/                    # App configuration, logging & database engines
│       ├── rag/                     # Context building, prompt generation & validation
│       ├── services/                # RAG service facade & hybrid search engine
│       ├── llm/                     # Dynamic AI provider abstraction (Gemini, Ollama, etc.)
│       ├── agent/                   # ReAct agent loop, tool executor & safety guardrails
│       ├── mcp/                     # Model Context Protocol (JSON-RPC 2.0) server
│       ├── observability/           # OpenTelemetry metrics, traces & health monitors
│       ├── schemas/                 # Pydantic V2 validation models (DTOs)
│       └── repositories/            # Legacy repository wrappers
│
├── processor/                       # Background Ingestion Microservice (Azure Functions)
│   ├── Dockerfile                   # Azure Functions Python worker container
│   ├── host.json                    # Function app host runtime settings
│   ├── local.settings.json.example  # Local Azurite connection template
│   ├── requirements.txt             # Document processing libraries (pypdf, docx, chroma)
│   ├── function_app.py              # Queue trigger handler & pipeline entry point
│   ├── extractors/                  # File parsers (PDF, DOCX, TXT)
│   ├── chunkers/                    # Legal-aware structural text chunkers
│   └── services/                    # ChromaDB indexing & vector synchronization
│
├── frontend/                        # Angular Single-Page Application (SPA)
│   ├── Dockerfile                   # Multi-stage Nginx build container
│   ├── nginx.conf                   # Production Nginx reverse-proxy & routing config
│   ├── angular.json                 # Angular build & dev server configuration (Port 4201)
│   ├── package.json                 # Frontend dependencies (Angular, Lucide, Tailwind)
│   ├── tsconfig.json                # TypeScript compiler configuration
│   └── src/                         # Application source code
│       ├── index.html               # Main HTML host
│       ├── main.ts                  # Application bootstrap
│       ├── styles.css               # Global Tailwind CSS styling
│       └── app/
│           ├── core/                # Singleton services, models, & HTTP interceptors
│           └── features/            # Feature modules (chat, contracts, agent-lab)
│
├── tests/                           # Consolidated Pytest Test Suite
│   ├── test_clean_domain.py         # Pure domain entities & value objects tests
│   ├── test_clean_use_cases.py      # Contract & document use cases tests
│   ├── test_extractors_and_chunkers.py # Text parsing & legal-aware chunking tests
│   ├── test_greetings_and_unsupported.py # Conversational routing & unique fallbacks
│   ├── test_hybrid_rag.py           # BM25 + Vector RRF ranking mathematics
│   ├── test_llm_providers.py        # Pluggable AI provider conformance tests
│   ├── test_rag_pipeline.py         # Grounded synthesis & citation verification
│   ├── test_mcp.py                  # Model Context Protocol JSON-RPC tests
│   ├── test_agent.py                # ReAct agent loop & tool execution tests
│   ├── test_multi_agent.py          # Multi-agent orchestrator & delegation tests
│   ├── test_production.py           # Production integration workflows & benchmarks
│   └── test_trajectory.py           # Agent trajectory & security guardrail tests
│
├── docs/                            # Enterprise Technical Documentation Suite
│   ├── architecture.md              # System architecture, workflows & sequence diagrams
│   ├── api.md                       # Complete OpenAPI REST & WebSocket specifications
│   ├── database.md                  # SQL Server 2022 schema, ERD & data dictionaries
│   ├── rag_pipeline.md              # Ingestion, chunking, embeddings & hybrid RRF search
│   ├── agent_mcp.md                 # Agent reasoning, tool bindings & MCP specifications
│   ├── deployment.md                # Docker Compose topology, secrets & troubleshooting
│   └── folder_structure.md          # This directory and file structure guide
│
├── shared-corpus/                   # Standard Benchmark Contracts & Ground Truth
│   ├── README.md                    # Corpus documentation & licensing
│   ├── contracts-pdf/               # Standardized legal contracts in PDF format
│   ├── contracts-docx/              # Standardized legal contracts in Word DOCX format
│   ├── contracts/                   # Extracted plain text contracts
│   ├── eval/                        # Golden benchmark Q&A evaluation datasets
│   └── loaders/                     # Corpus ingestion helper scripts
│
├── config/                          # MCP Server & Tool Configurations
│   ├── mcp_server1_only.json        # Single-server MCP configuration profile
│   └── mcp_servers_all.json         # Multi-server MCP configuration profile
│
├── resource/                        # Benchmark Traces, Logs & Architectural Reports
│   ├── agent_card.json              # Autonomous agent capability manifest
│   ├── eval_dataset_25.json         # Standard 25-question evaluation suite
│   ├── labels_25.json               # Ground truth answers and clause references
│   └── trace.json                   # Sample execution trace for agent ReAct loop
│
└── scripts/                         # Operational & Automation Scripts
    ├── evaluate_shared_corpus.py    # Automated Golden Set benchmark evaluator
    ├── ingest_shared_corpus_to_ui.py# Bulk ingestion script for shared legal corpus
    └── test_docker_workflow.py      # Automated Docker end-to-end integration verifier
```

---

## 🔍 In-Depth Breakdown by Directory

---

### 1. Root Directory (`/`)

Contains environment templates, orchestration files, and cross-cutting project definitions:

| File | Use Case & Purpose | Key Contents |
|---|---|---|
| `.env.example` | Template for environment variables. Developers copy this to `.env` to configure ports, database credentials, and active AI keys. | Pre-configured for local Azurite, SQL Server SA password, and Gemini / Ollama toggles with zero leaked secrets. |
| `docker-compose.yml` | Multi-container orchestrator that starts the entire enterprise stack with a single command. | Defines 7 services: `legal_frontend` (4201), `legal_backend` (8080), `legal_processor` (7071), `legal_chromadb` (8000), `legal_sqlserver` (1433), `legal_azurite` (10000-10002), `legal_ollama` (11434). |
| `Dockerfile` | Root Docker image definition bundling backend, processor utilities, and test suites. | Based on `python:3.11-slim`, installs Microsoft ODBC 17/18 drivers for SQL Server, bundles dependencies, and configures the test harness. |
| `run_capstone.py` | Single entry-point script to run the full verification and evaluation benchmark. | Executes tests, runs RAG evaluations against the shared corpus, verifies MCP tools, and produces an evaluation report. |
| `README.md` | Front-door documentation for onboarding developers and system operators. | Quickstart instructions, feature highlights, service port maps, and testing commands. |
| `architecture.md` | Executive-level architecture summary. | High-level component overview and sequence summaries. |

---

### 2. `backend/` — API & AI Orchestration Core

The `backend/` folder contains the primary FastAPI application. It is structured strictly using **Clean Architecture** so that business rules do not depend on external frameworks.

#### `backend/app/domain/` (Pure Business Logic)
The core heart of the system. It contains zero dependencies on FastAPI, SQLAlchemy, or HTTP clients.
* **`entities/`**: Plain Python dataclasses representing business models:
  * `contract_entity.py`: Represents a legal contract agreement.
  * `document_entity.py`: Represents an attached document file, tracking its `page_count` and processing status.
  * `conversation_entity.py`: Represents chat sessions, user questions, assistant answers, and citations (`RAGSource`).
* **`value_objects/`**: Immutable attributes with built-in validation (e.g., `contract_number.py`, `date_range.py`).
* **`ports/`**: Abstract interfaces (ABCs) that declare what the domain needs without specifying how it's implemented:
  * `repositories/`: `contract_repository_port.py`, `document_repository_port.py`, `chat_repository_port.py`.
  * `unit_of_work_port.py`: Transaction manager interface.
* **`enums.py`**: Business state enums (`ContractStatus`, `DocumentStatus`, `MessageRole`, `JobStatus`).
* **`exceptions/`**: Domain-specific error types (`ContractNotFoundException`, `DocumentNotFoundException`).

#### `backend/app/application/` (Use Cases)
Orchestrates domain entities to fulfill specific business operations:
* **`contracts/contract_use_cases.py`**: Creation, retrieval, amendment linking, and archiving of contracts.
* **`documents/document_use_cases.py`**: Document metadata querying, status updates, and soft deletion.
* **`documents/upload_document_use_case.py`**: Validates file uploads, stores blobs in Azurite, and enqueues background processing jobs.
* **`chat/chat_use_cases.py`**: Manages the conversation lifecycle, persists user messages, triggers the RAG service, and saves assistant responses with citations.

#### `backend/app/infrastructure/` (Adapters & External Integrations)
Implements the interfaces declared in `domain/ports/`:
* **`database/`**:
  * `repositories/`: Concrete SQLAlchemy implementations (`contract_repository_impl.py`, `document_repository_impl.py`, `chat_repository_impl.py`).
  * `mappers/`: Bidirectional converters between SQLAlchemy database models and pure domain entities (`contract_mapper.py`, `document_mapper.py`, `chat_mapper.py`).
  * `unit_of_work.py`: SQLAlchemy Unit of Work implementation for atomic database transactions.
* **`storage/azure_storage.py`**: Interacts with Azure Blob Storage / Azurite emulator to store uploaded contract files.
* **`queue/azure_queue.py`**: Interacts with Azure Storage Queue to post document processing jobs.
* **`vector/vector_client.py`**: HTTP client connecting the backend to ChromaDB for vector retrieval.

#### `backend/app/api/v1/` (REST API Controllers)
FastAPI routers that accept HTTP requests, validate input schemas, and call application use cases:
* `contracts.py`: Endpoints for creating, listing, updating, and viewing contracts (`/api/v1/contracts`).
* `documents.py`: Endpoints for file upload, listing documents per contract, and document status checks (`/api/v1/documents`).
* `chat.py`: Endpoints for creating conversations, viewing message history, and submitting questions (`/api/v1/chat`).
* `search.py`: Direct vector and hybrid search endpoints for testing retrieval.
* `processing.py`: Ingestion job progress tracking and status endpoints.
* `agent.py`: Agent execution endpoints for autonomous legal analysis.
* `mcp_api.py`: REST inspection endpoints for Model Context Protocol tools.
* `websocket.py`: Full-duplex WebSocket router for real-time document processing notifications (`/ws/processing/{client_id}`).

#### `backend/app/rag/` & `backend/app/services/` (RAG Engine)
* **`services/rag_service.py`**: The enterprise RAG facade (`EnterpriseRAGService`). Directs incoming queries to either the dynamic greeting handler or the hybrid retrieval pipeline.
* **`services/hybrid_search_service.py`**: Implements **Reciprocal Rank Fusion (RRF)**, combining BM25 keyword search scores with dense vector cosine similarity.
* **`rag/context_builder.py`**: Formats retrieved chunk snippets into a structured `<context>` block with clear document and section headers.
* **`rag/citation_handler.py`**: Extracts document names, page numbers, sections, and relevance scores into structured citation DTOs.
* **`rag/prompt_builder.py`**: Generates standardized, provider-independent prompts enforcing strict legal grounding and amendment hierarchy rules.
* **`rag/response_validator.py`**: Post-processes LLM responses. Strips reasoning tokens (`<thought>...</thought>`), verifies citation integrity, and triggers dynamic fallbacks if the context is insufficient.

#### `backend/app/llm/` (Dynamic Multi-Provider AI Engine)
Provides an abstract base provider (`base.py`) and pluggable implementations:
* `gemini_provider.py`: Google Gemini API integration (`gemma-4-26b-a4b-it`, `gemini-embedding-001`).
* `ollama_provider.py`: Local Ollama integration for air-gapped or offline execution (`llama3.2`, `nomic-embed-text`).
* `openai_provider.py` & `openrouter_provider.py`: Commercial cloud provider integrations.
* `factory.py`: Dynamically instantiates the active provider based on the `AI_PROVIDER` environment variable.

#### `backend/app/agent/` & `backend/app/mcp/` (Agent & MCP Subsystem)
* **`agent/orchestrator.py`**: Implements ReAct (Reason + Act) loops allowing autonomous multi-step reasoning over contracts.
* **`agent/guardrails.py`**: Deterministic safety filters intercepting requests for unauthorized legal advice.
* **`mcp/server.py`**: Implements the Model Context Protocol (MCP) JSON-RPC 2.0 server over standard I/O and HTTP, exposing safe database tools (`list_contracts`, `search_clauses`) to AI agents.

---

### 3. `processor/` — Document Ingestion Microservice

The `processor/` directory contains an independent **Azure Functions Python worker**. It runs in a separate Docker container (`legal_processor:7071`) to keep heavy document parsing out of the FastAPI request/response path.

| Component / Subfolder | Purpose & Description |
|---|---|
| `function_app.py` | The main entry point. Listens to the `legal-document-processing` Azure Storage Queue. When a new file is uploaded, this function triggers automatically, coordinates extraction, chunking, and indexing, and updates the database status. |
| `extractors/` | Specialized file format text parsers: <br>• `pdf_extractor.py`: Extracts text and page numbers from PDF files using `pypdf`.<br>• `docx_extractor.py`: Extracts text and paragraph hierarchies from Microsoft Word files.<br>• `txt_extractor.py`: Parses UTF-8 and ASCII plain text documents. |
| `chunkers/` | Document splitters: <br>• `legal_chunker.py` (`LegalAwareChunker`): Recognizes structural legal boundaries (`Article`, `Section`, `Clause`, `Recital`, `Schedule`) to prevent cutting clauses in half.<br>• `recursive_chunker.py`: Fallback character chunker for unstructured sections. |
| `services/chroma_service.py` | Connects to ChromaDB. Features **self-healing dimensionality detection** that automatically adapts the vector collection when switching between 768-dim (Ollama) and 3072-dim (Gemini) embeddings. |
| `host.json` | Azure Functions host configuration defining logging levels and extension bundles. |
| `requirements.txt` | Minimal Python dependencies required for document extraction and vector indexing. |

---

### 4. `frontend/` — Angular Single-Page Application

The frontend is an enterprise web interface built with **Angular 19**, **Tailwind CSS**, and **Lucide Icons**, served via **Nginx** on **port 4201**.

| Folder / File | Purpose & Contents |
|---|---|
| `nginx.conf` | Production web server configuration. Serves compiled Angular assets and reverse-proxies `/api/` and `/ws/` calls to the FastAPI backend. |
| `angular.json` | Project configuration specifying compilation rules, assets, and development port `4201`. |
| `src/app/core/` | Application-wide infrastructure: <br>• `services/`: API services (`contract.service.ts`, `chat.service.ts`, `websocket.service.ts`).<br>• `models/`: TypeScript interfaces representing contracts, messages, and citations. |
| `src/app/features/contracts/` | Contract management dashboard. Displays contract portfolios, file upload modals, processing status badges, and document viewer links. |
| `src/app/features/chat/` | Conversational RAG interface. Supports conversation creation, message history, streaming responses, and clickable citation pills showing exact source sections and page numbers. |
| `src/app/features/agent-lab/` | Experimental UI for inspecting ReAct agent reasoning steps, tool invocation traces, and multi-agent communications. |

---

### 5. `tests/` — Consolidated Test Suite

All automated tests are centralized in the root `tests/` folder to ensure unified execution with `pytest`:

```
tests/
├── test_clean_domain.py             # 5 Tests: Domain entities, date range validation, value objects
├── test_clean_use_cases.py          # 4 Tests: Contract and document use cases, mocking
├── test_extractors_and_chunkers.py  # 3 Tests: PDF/DOCX extractors, legal-aware chunking boundaries
├── test_greetings_and_unsupported.py# 35 Tests: Greetings, identity queries, dynamic fallback generation
├── test_hybrid_rag.py               # 4 Tests: BM25 tokenization, RRF rank fusion mathematics, tenant isolation
├── test_llm_providers.py            # 4 Tests: Provider switching, conformance, error handling
├── test_rag_pipeline.py             # 4 Tests: Grounded synthesis, empty retrieval handling, output validator
├── test_mcp.py                      # 3 Tests: Model Context Protocol discovery, tool schema validation
├── test_agent.py                    # 3 Tests: ReAct agent loop, tool invocation, safety guardrails
├── test_multi_agent.py              # 4 Tests: Multi-agent coordination, subtask delegation
├── test_production.py               # 3 Tests: Live container health, end-to-end integration workflows
└── test_trajectory.py               # 5 Tests: Argument validation guardrails, prompt injection mitigation
```

* **Total Passing Tests**: **72 passed, 0 failed**.
* **Execution Command**:
  ```powershell
  pytest tests/ -v
  # Inside Docker:
  docker exec legal_backend pytest tests/ -v
  ```

---

### 6. `shared-corpus/` — Benchmark Legal Documents

Contains reference contracts representing realistic enterprise legal relationships:

* **`contracts-pdf/` & `contracts-docx/`**: Formatted original agreements:
  1. `MSA-2026-014_Northwind_Master_Services_Agreement`: Baseline master agreement.
  2. `AMD-2026-014-01_Northwind_Amendment_No_1`: Amendment modifying liability caps.
  3. `AMD-2026-014-02_Northwind_Amendment_No_2`: Amendment overriding payment and late interest terms.
  4. `SCH-2026-014_Northwind_Schedules`: Attached service level and fee schedules.
  5. `MSA-2026-022_Vertex_Master_Services_Agreement`: Second distinct vendor contract (tests tenant isolation).
  6. `NDA-2026-007_Mutual_Non_Disclosure_Agreement`: Standard confidentiality agreement.
* **`eval/golden_set.json`**: Ground-truth Q&A dataset with exact clause citations used by automated evaluation scripts to verify retrieval accuracy and prevent regressions.

---

### 7. `docs/` — Technical Documentation Suite

This directory contains deep-dive enterprise documentation for every subsystem:

| Documentation File | Subject Covered |
|---|---|
| `architecture.md` | System microservices topology, trust boundaries, sequence diagrams, and fault-tolerance matrix. |
| `api.md` | Complete OpenAPI catalog across all 8 routers with request/response JSON schemas. |
| `database.md` | SQL Server 2022 schema, ER diagram, 7 table data dictionaries, and migration guide. |
| `rag_pipeline.md` | Detailed explanation of extraction, chunking, embeddings, ChromaDB, and hybrid RRF search. |
| `agent_mcp.md` | ReAct reasoning loops, Model Context Protocol (MCP JSON-RPC 2.0), and safety guardrails. |
| `deployment.md` | Docker Compose production topology, environment variable matrix, and troubleshooting playbook. |
| `folder_structure.md` | *(This File)* Detailed structural breakdown and file dictionary. |

---

### 8. `scripts/`, `config/` & `resource/`

Supporting assets for operations, benchmarks, and tooling:

* **`scripts/`**:
  * `ingest_shared_corpus_to_ui.py`: Automates uploading and indexing all shared corpus files via the REST API.
  * `evaluate_shared_corpus.py`: Runs automated benchmark evaluations against `eval/golden_set.json` and outputs Hit@K and MRR metrics.
  * `test_docker_workflow.py`: Validates health, file uploads, and chat responses against the live Docker stack.
* **`config/`**:
  * `mcp_servers_all.json`: Standard client configuration registering the local Legal MCP server for AI clients.
* **`resource/`**:
  * Contains evaluation results, latency matrices, execution traces (`trace.json`), and cost analysis reports.

---

## 🚀 Developer Navigation Quick-Reference

When contributing to this codebase, use this map to know where changes belong:

| If you want to... | Look in this directory: |
|---|---|
| **Add a new REST API endpoint** | `backend/app/api/v1/` and `backend/app/schemas/` |
| **Add a new business use case** | `backend/app/application/` |
| **Add a database table or column** | `backend/app/domain/models/`, `backend/app/domain/entities/`, and `backend/alembic/` |
| **Add support for a new document format** | `processor/extractors/` |
| **Modify chunking rules for legal clauses** | `processor/chunkers/legal_chunker.py` |
| **Change the prompt or citation format** | `backend/app/rag/prompt_builder.py` and `citation_handler.py` |
| **Integrate a new AI Model or Provider** | `backend/app/llm/providers/` and register in `factory.py` |
| **Add a new MCP tool for agents** | `backend/app/mcp/server.py` |
| **Add or update automated tests** | `tests/` |
| **Update UI views or styles** | `frontend/src/app/features/` |
