# Enterprise Legal Contract Assistant - System Architecture & Technical Specification

> **System Name**: Legal Contract Assistant  
> **Repository**: `legal-contract-rag`  
> **Version**: 2.0  
> **Primary Use Case**: Enterprise-grade Retrieval-Augmented Generation (RAG) for legal contract ingestion, clause extraction, document scoping, and verifiable AI Q&A.

---

## 1. System Architecture Overview

The system is built as an event-driven, containerized microservices platform consisting of **7 decoupled core services**:

```
                               ┌──────────────────────────┐
                               │     Angular 17+ UI       │
                               │     (legal_frontend)     │
                               └────────────┬─────────────┘
                                            │ HTTP / REST / WebSockets
                                            ▼
                               ┌──────────────────────────┐
                               │      FastAPI Gateway     │
                               │      (legal_backend)     │
                               └──────┬──┬────────────┬───┘
               SQL Transactions       │  │            │ Azure Queue Jobs
       ┌──────────────────────────────┘  │            └──────────────────────────────┐
       ▼                                 ▼                                           ▼
┌───────────────┐               ┌─────────────────┐                        ┌──────────────────┐
│  MS SQL 2022  │               │   Ollama / LLM  │                        │ Azurite Storage  │
│(legal_sqlserver)              │(Ollama/Gemini/..)│                        │ (Blobs & Queues) │
└───────────────┘               └─────────────────┘                        └────────┬─────────┘
                                                                                    │
                                                                   Async Queue Trigger
                                                                                    │
                                                                                    ▼
                               ┌──────────────────────────┐                ┌──────────────────┐
                               │   Vector Database        │◄───────────────┤ Azure Functions  │
                               │   (legal_chromadb)       │ Vector Indexing│ (legal_processor)│
                               └──────────────────────────┘                └──────────────────┘
```

### Microservices Breakdown

1. **`legal_frontend`** (Angular 17+ / Nginx)
   - Serves the Single Page Application (SPA).
   - Handles Contract Explorer, Document Repository, Chat Interface, Citation Drawer, and WebSocket status broadcasts.
   - Configured with `client_max_body_size 50M` in Nginx for large document uploads.

2. **`legal_backend`** (FastAPI / Python 3.11)
   - Enterprise REST API gateway handling CRUD operations, database ORM, RAG orchestration, and WebSocket real-time updates.
   - Enforces contract-scoped metadata filtering and lazy chat session creation.

3. **`legal_processor`** (Azure Functions v4 / Python 3.11)
   - Dedicated background queue worker running event-driven document processing jobs.
   - Performs text extraction (PDF, DOCX, TXT), legal-aware chunking, batch embedding generation, and ChromaDB vector indexing.

4. **`legal_sqlserver`** (Microsoft SQL Server 2022)
   - Relational metadata store for Contracts, Documents, Conversations, Messages, Processing Jobs, and RAG Sources.

5. **`legal_azurite`** (Azure Storage Emulator)
   - Emulates Azure Blob Storage (for original file storage) and Azure Queue Storage (`legal-document-processing` queue).

6. **`legal_chromadb`** (ChromaDB Vector Server 0.5.0)
   - Vector database storing dense text chunk embeddings with metadata tags (`contract_id`, `document_id`, `page_number`, `section`, `clause`).

7. **`ollama`** (Local LLM & Embedding Server)
   - Hosts `nomic-embed-text` (for 768-dim embeddings) and `llama3.2` (for grounded legal generation). Fallback support for OpenRouter, OpenAI, and Google Gemini.

---

## 2. Comprehensive File Directory & Component Responsibilities

```
legal-contract-rag/
├── docker-compose.yml              # Multi-container orchestration specification
├── .env                            # Environment variables & provider configurations
├── ARCHITECTURE.md                 # System Architecture & Technical Specification
│
├── backend/                        # FastAPI Enterprise Gateway Service
│   ├── Dockerfile                  # Python 3.11-slim container with MS ODBC Driver 17/18
│   ├── requirements.txt            # FastAPI, SQLAlchemy 2.0, PyODBC, Alembic, HTTPX dependencies
│   ├── scripts/
│   │   └── start.sh                # Entrypoint script: ODBC driver check, migrations, Uvicorn launch
│   ├── alembic/                    # Database Schema Migration Manager
│   │   ├── env.py
│   │   └── versions/               # DDL migration versions for SQL Server
│   └── app/
│       ├── main.py                 # FastAPI application initialization, CORS, router mounting
│       ├── core/
│       │   ├── config.py           # Pydantic BaseSettings environment configuration
│       │   └── database.py         # SQLAlchemy Engine, SessionLocal factory, PyODBC connection pool
│       ├── domain/models/          # SQLAlchemy ORM Data Models
│       │   ├── contract.py         # Contract model (contract_number auto-generation & uniqueness)
│       │   ├── document.py         # Document model (linked to Contract, tracks page_count & status)
│       │   ├── chunk.py            # DocumentChunk model (structural legal attributes)
│       │   ├── conversation.py     # Conversation model (session scoping & soft deletion)
│       │   ├── message.py          # Message model (User/Assistant roles, linked to Conversation)
│       │   ├── rag_source.py       # RAGSource model (Citations linked to Assistant Message)
│       │   └── processing_job.py   # ProcessingJob model (Async job correlation & retry tracking)
│       ├── repositories/           # Data Access Layer (Repository Pattern)
│       │   ├── contract_repository.py # Auto-generates contract numbers, handles IntegrityErrors
│       │   ├── document_repository.py # CRUD & contract filtering for documents
│       │   ├── chat_repository.py     # Session messages CRUD & non-empty conversation filtering
│       │   └── job_repository.py      # Background job status & correlation tracking
│       ├── schemas/                # Pydantic Schemas (Data Transfer Objects)
│       │   ├── contract.py         # ContractCreate, ContractUpdate, ContractResponse
│       │   ├── document.py         # DocumentUploadResponse, DocumentResponse (includes contract_name)
│       │   ├── chat.py             # ChatRequest, ChatResponse, ConversationResponse, SourceDTO
│       │   └── processing.py       # ProcessingJobResponse, JobStatusUpdate
│       ├── services/               # Core Business Logic & External Integrations
│       │   ├── storage_service.py  # Azure Blob Storage Client (upload, download, delete)
│       │   ├── queue_service.py    # Azure Queue Storage Client (enqueue document processing jobs)
│       │   ├── embedding_service.py# Batched Embedding Generator (Ollama, Gemini, OpenAI, OpenRouter)
│       │   └── rag_service.py      # EnterpriseRAGService orchestrator (Vector Search + LLM + Citations)
│       ├── infrastructure/
│       │   └── vector/
│       │       └── vector_client.py# Internal HTTP client calling Document Processor Vector APIs
│       ├── llm/                    # Provider-Independent LLM Abstraction Layer
│       │   ├── base.py             # Base LLMProvider abstract class & LLMRequest/LLMResponse models
│       │   ├── factory.py          # LLMProviderFactory resolving active provider dynamically
│       │   ├── exceptions.py       # Standardized LLMProviderError exceptions
│       │   └── providers/          # Provider Adapters
│       │       ├── ollama.py       # Ollama native API client
│       │       ├── openrouter.py   # OpenRouter API client
│       │       ├── openai.py       # OpenAI API client
│       │       └── gemini.py       # Google Gemini API client
│       ├── rag/                    # Standardized RAG Pipeline Components
│       │   ├── context_builder.py  # Assembles retrieved chunk text into structured context
│       │   ├── citation_handler.py # Formats chunk metadata into SourceDTO citations
│       │   ├── prompt_builder.py   # System & User prompt templates for legal compliance
│       │   └── response_validator.py# Cleans LLM output & handles fallback responses
│       └── api/v1/                 # REST API Controllers & WebSockets
│           ├── contracts.py        # /api/v1/contracts endpoints
│           ├── documents.py        # /api/v1/documents endpoints (file size validation <= 25MB)
│           ├── chat.py             # /api/v1/chat endpoints (conversation & message routing)
│           ├── processing.py       # /api/v1/processing endpoints (patch job status)
│           └── ws.py               # /api/v1/ws/events WebSocket connection manager
│
├── processor/                      # Async Azure Functions Worker Service
│   ├── Dockerfile                  # Azure Functions Python 4-python3.11 base image
│   ├── host.json                   # Functions host config (maxPollingInterval: 2s)
│   ├── requirements.txt            # PyODBC, chromadb==0.5.0, numpy==1.26.4, python-docx, pypdf
│   ├── function_app.py             # Main Queue Trigger (`LegalDocumentQueueTrigger`) & HTTP routes
│   └── services/
│       ├── document_parser.py      # Multi-format text extractor (PDF, DOCX, TXT)
│       ├── chunker.py              # `LegalAwareChunker` (Article/Section/Clause regex & fallback splitting)
│       ├── embedding_service.py    # `ProcessorEmbeddingService` with 10-item batching
│       └── chroma_service.py       # `ProcessorChromaService` (Lazy collection init & vector search)
│
└── frontend/                       # Angular 17+ Web Application
    ├── Dockerfile                  # Multi-stage Angular build + Nginx production server
    ├── nginx.conf                  # Nginx proxy (client_max_body_size 50M, API proxying)
    ├── src/
    │   ├── index.html              # Title: "Legal Contract Assistant"
    │   ├── app/
    │   │   ├── app.component.ts    # Main layout & tab state manager ('contracts', 'documents', 'chat')
    │   │   ├── app.component.html  # Header, Brand Logo ("Legal Contract Assistant v2.0"), Workspace
    │   │   ├── core/
    │   │   │   ├── models.ts       # TypeScript interfaces (Contract, Document, Conversation, Message)
    │   │   │   └── services/
    │   │   │       ├── contract.service.ts # Contract CRUD HTTP service
    │   │   │       ├── document.service.ts # Document upload & management HTTP service
    │   │   │       ├── chat.service.ts     # Chat & conversation session HTTP service
    │   │   │       └── websocket.service.ts# Real-time WebSocket event listener
    │   │   └── features/
    │   │       ├── contracts/
    │   │       │   ├── contract-list/      # Left sidebar listing contracts
    │   │       │   ├── contract-detail/    # Center panel with upload button & document list
    │   │       │   └── all-documents/      # Global document repository table with Contract Name column
    │   │       └── chat/
    │   │           ├── chat-window/        # Multi-turn chat, lazy session creation, scope badge
    │   │           └── citation-drawer/    # Slide-over panel displaying source chunk citations
```

---

## 3. Data Processing Pipelines & Execution Workflows

### Workflow A: Contract Creation & Unique Constraint Handling

```
User (UI) ──> POST /api/v1/contracts ──> ContractRepository.create()
                                                  │
                                                  ├──> Is contract_number missing/empty?
                                                  │    YES: Generate "CNT-XXXXXXXX"
                                                  │
                                                  └──> Save to MS SQL Server
                                                       (Catches IntegrityError -> returns 400 Bad Request)
```

1. User creates a contract in the UI.
2. If `contract_number` is omitted or empty, `ContractRepository` generates a unique string formatted as `CNT-{uuid[:8].upper()}` (e.g., `CNT-1902C5F5`).
3. SQL Server saves the row cleanly without `NULL` duplicate key constraint violations (`UQ__Contract__1CA37CCEE555A18D`).

---

### Workflow B: Document Upload & Async Processing Pipeline

```
[1. UI Upload]
  │ (File <= 25MB)
  ▼
[2. Nginx Proxy] ──(client_max_body_size 50M)──> [3. FastAPI backend]
                                                      │
                                                      ├──> Save file to Azurite Blob Storage
                                                      ├──> Insert record in SQL Server (Status: "Queued")
                                                      └──> Push message to Azurite Storage Queue
                                                                  │
                                                                  ▼ (Poll interval: 2s)
                                                       [4. Azure Functions Processor]
                                                                  │
                                                                  ├──> Download Blob
                                                                  ├──> DocumentParser (Extract PDF/DOCX/TXT)
                                                                  ├──> LegalAwareChunker (Split into clauses)
                                                                  ├──> ProcessorEmbeddingService (Batched Embeddings)
                                                                  ├──> ProcessorChromaService (Index into ChromaDB)
                                                                  │
                                                                  ▼
                                                       [5. PATCH /api/v1/processing/jobs/{id}/status]
                                                                  │
                                                                  ├──> Update SQL Server (Status: "Completed", page_count)
                                                                  └──> Broadcast WebSocket "JOB_UPDATE" to UI
```

---

### Workflow C: Contract-Scoped vs. Global RAG Q&A Pipeline

```
[1. User Sends Question]
  │
  ▼
[2. Frontend Lazy Check] ──(If conversationId is null)──> Create Session first, then send prompt
  │
  ▼
[3. POST /api/v1/chat/conversations/{id}/messages]
  │
  ▼
[4. EnterpriseRAGService.answer_question()]
  │
  ├──> Generate Query Embedding via EmbeddingService
  │
  ├──> Vector Similarity Search via Processor Vector API
  │    │
  │    ├──> IF Scoped Contract Selected:
  │    │    Apply ChromaDB Filter: where={"contract_id": "selected_id"} (0% Cross-Contract Leakage)
  │    │
  │    └──> IF Global Mode:
  │         Omit `where` filter (Search across all contracts)
  │
  ├──> ContextBuilder: Format top_k chunks into structured prompt context
  ├──> CitationHandler: Build SourceDTOs (Document Name, Page, Section, Clause, Score)
  ├──> LLMProvider: Execute generation via Ollama / Gemini / OpenAI
  └──> ResponseValidator: Clean output text
  │
  ▼
[5. Persist to SQL Server]
  │
  ├──> Save Assistant Message linked to conversation_id
  └──> Save RAGSources linked to message_id
  │
  ▼
[6. Render UI Response] ──> Display Answer + "View Source Citations" Button
```

---

## 4. Key Architectural Patterns & Guarantees

1. **Strict Metadata Scoping**:
   - Every text chunk indexed in ChromaDB contains metadata: `{"contract_id": "...", "document_id": "...", "page_number": X, "clause": "..."}`.
   - When asking a question inside a contract scope, ChromaDB executes a pre-filter (`where={"contract_id": cid}`), ensuring complete data isolation and 0% cross-contract hallucination.

2. **Lazy Conversation Session Management**:
   - The UI maintains a clean local draft state (`New Conversation`).
   - Database rows for `Conversations` are created **only when the user sends their first question**, keeping the database free of empty junk sessions.
   - Backend `list_conversations()` filters with `Conversation.messages.any()`.

3. **Batched Embedding Processing**:
   - Both backend and processor services generate text embeddings in batches of 10–20 items.
   - Supports large legal documents (up to 25MB–50MB) with hundreds of pages without hitting Ollama or HTTP payload limits.

4. **Resilient Error Boundaries**:
   - Relational database constraint errors (e.g. duplicate contract numbers) are caught, rolled back, and returned as HTTP `400 Bad Request` rather than crashing Uvicorn with HTTP `500`.

---

## 5. Quick Command Reference

```bash
# Full Build and Start
docker compose up --build -d

# Build Only Specific Service
docker compose up --build -d frontend
docker compose up --build -d backend
docker compose up --build -d processor

# Live File Copy (No Rebuild Required)
docker cp backend/app/api/v1/documents.py legal_backend:/app/backend/app/api/v1/documents.py
docker cp processor/services/embedding_service.py legal_processor:/home/site/wwwroot/services/embedding_service.py
docker restart legal_backend legal_processor
```
