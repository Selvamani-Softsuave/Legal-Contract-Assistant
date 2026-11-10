# Enterprise System Architecture Document

**System Name**: Enterprise Legal Contract Review Assistant & Grounded RAG Platform  
**Architecture Style**: Distributed Microservices & Hexagonal (Ports & Adapters) Clean Architecture  
**Document Version**: `2.0.0` (Production Reference Architecture)  
**Date**: November 2026  

> [!NOTE]
> This canonical document specifies the end-to-end architecture of the Legal Contract RAG & Assistant System. For specialized modular specifications, see:
> - [`docs/api.md`](docs/api.md) — Complete REST & WebSocket API Specification
> - [`docs/database.md`](docs/database.md) — SQL Server Schema & Entity Relationship Specification
> - [`docs/rag_pipeline.md`](docs/rag_pipeline.md) — Ingestion, Chunking, Embeddings, & Grounded Retrieval
> - [`docs/agent_mcp.md`](docs/agent_mcp.md) — ReAct Agent, Multi-Agent Orchestration, & Model Context Protocol (MCP)
> - [`docs/deployment.md`](docs/deployment.md) — Docker Compose Infrastructure, Environment Variables, & Runbooks

---

## 1. System Overview & Core Architectural Principles

The Enterprise Legal Contract Review Assistant is an AI-powered system designed for corporate legal departments, procurement teams, and compliance officers. It automates contract ingestion, structural clause parsing, temporal amendment supersession resolution, and grounded question answering with precise citations.

### Core Architectural Principles:

1. **Hexagonal Clean Architecture**:
   Domain logic (entities, validation, value objects) is decoupled from external frameworks, databases, and LLM providers. Adapters implement domain ports via inversion of control, ensuring testability and longevity.

2. **Decoupled Agent-Tool Boundary (Model Context Protocol)**:
   The agent host contains zero hardcoded tool definitions. All capabilities, parameter schemas, and documentation are discovered dynamically at runtime from independent MCP servers via JSON-RPC 2.0.

3. **Temporal Grounding & Amendment Hierarchy**:
   Legal contracts operate under an amendment hierarchy. The system prioritizes later executed amendments over earlier baseline provisions, guaranteeing that superseded terms are never cited as governing obligations.

4. **Dynamic AI Provider Agnosticism**:
   Eliminates single-vendor AI lock-in. A unified provider abstraction layer supports switching between Google Gemini, local Ollama, OpenRouter, and OpenAI through configuration variables without changing application code.

5. **Asynchronous Decoupled Ingestion**:
   Heavy document extraction, OCR, structural chunking, and vector embedding are offloaded to an asynchronous Azure Functions queue worker, ensuring web API responsiveness and system scalability.

---

## 2. High-Level Architecture Diagram

```mermaid
flowchart TD
    subgraph ClientTier["Client Tier (Port 4201)"]
        UI["Angular 19 Standalone SPA\n- Chat & Citation Inspector\n- Contract & Document Manager\n- Agent & MCP Lab"]
        Nginx["Nginx Reverse Proxy\n(Port 4201:80)"]
        UI --> Nginx
    end

    subgraph APITier["Backend API Gateway (Port 8080)"]
        FastAPI["FastAPI 0.111 Application\n(/api/v1/*, /health)"]
        Nginx -->|Proxy /api/| FastAPI
        Nginx -->|Proxy /ws/| FastAPI
        
        Middlewares["Cross-Cutting Middlewares\n- Distributed Correlation ID\n- RFC 7807 Error Handlers\n- CORS Policies"]
        FastAPI --- Middlewares
        
        AppServices["Application Services\n- ChatUseCases / RAGService\n- ContractUseCases\n- DocumentUseCases\n- MCPAgentHost / MultiAgent"]
        FastAPI --> AppServices
    end

    subgraph IngestionTier["Background Processing Tier (Port 7071)"]
        QueueTrigger["Azure Functions Python v2 Worker\n(Queue Trigger: legal-document-processing)"]
        Extractors["Extractors & Chunkers\n- PdfExtractor (pdfplumber)\n- DocxExtractor (python-docx)\n- LegalAwareChunker"]
        VectorService["Processor Chroma & Embedding Adapter\n(HTTP Vector Search & Ingestion)"]
        
        QueueTrigger --> Extractors
        Extractors --> VectorService
    end

    subgraph StorageTier["Data & Persistence Tier"]
        SQLServer[("Microsoft SQL Server 2022\n(Port 1433)\nTables: Contracts, Documents, Jobs, Chats")]
        Azurite[("Azure Storage / Azurite Emulator\n- Blob Storage (Port 10000)\n- Queue Storage (Port 10001)")]
        ChromaDB[("ChromaDB 0.5.20\n(Port 8000)\nCollection: legal_contracts (HNSW Cosine)")]
        
        AppServices -->|Metadata & Message History| SQLServer
        AppServices -->|File Uploads & Enqueue Jobs| Azurite
        QueueTrigger -->|Read Queue & Download Blobs| Azurite
        QueueTrigger -->|Update Job Status| SQLServer
        VectorService -->|Add Vectors & Metadatas| ChromaDB
        AppServices -->|Dense Vector Retrieval| VectorService
    end

    subgraph ExternalAITier["Dynamic AI Provider Tier"]
        Gemini["Google Gemini API\n- LLM: gemma-4-26b-a4b-it\n- Embed: gemini-embedding-001 (3072 dim)"]
        Ollama["Local Ollama Service (Port 11434)\n- LLM: llama3.2\n- Embed: nomic-embed-text (768 dim)"]
        OpenRouter["OpenRouter / OpenAI APIs\n- LLM: openrouter/free\n- Embed: text-embedding-3-small"]
        
        AppServices -->|Active LLM Generation| Gemini
        VectorService -->|Batch Vector Embeddings| Gemini
        AppServices -.->|Fallback / Switch| Ollama
        VectorService -.->|Fallback / Switch| Ollama
    end
```

---

## 3. Component Responsibilities & Technology Stack

| Layer / Component | Technology | Responsibilities |
|---|---|---|
| **Frontend SPA** | Angular 19, TypeScript 5.5, Tailwind CSS, RxJS | Interactive legal chat, contract and document management, real-time WebSocket job tracking, grounded source citation drawer, agent experimental lab. |
| **Ingress Proxy** | Nginx Alpine (Docker) | Static asset serving, SSL/TLS termination, reverse proxy routing for `/api/` (HTTP) and `/ws/` (WebSocket). |
| **Backend API Gateway** | FastAPI, Python 3.11, Uvicorn | Request validation (Pydantic V2), correlation ID injection, RFC 7807 problem details formatting, business use case orchestration. |
| **RAG Orchestrator** | `EnterpriseRAGService`, `ContextBuilder`, `ResponseValidator` | Conversational routing, hybrid retrieval fusion (BM25 + Dense vector), amendment hierarchy enforcement, reasoning trace normalization. |
| **Agent Subsystem** | `ReActAgent`, `FixedDeterministicWorkflow`, `MultiAgentOrchestrator` | Iterative Thought-Action-Observation loops, deterministic workflows, multi-agent worker delegations, budget tracking, prompt injection testing. |
| **MCP Host & Servers** | `MCPAgentHost`, `MCPClientManager`, `ClauseServer`, `RepoServer` | Decoupled runtime tool discovery over JSON-RPC 2.0, wire tracing, deterministic legal advice refusal guardrails. |
| **Document Processor** | Azure Functions Python v2 Worker | Asynchronous queue-triggered worker, document extraction (PDF/DOCX/TXT), structural legal chunking, vector embedding generation. |
| **Relational Database** | Microsoft SQL Server 2022 | Entity metadata persistence, relational integrity, foreign key cascading, conversation history, audit logging. |
| **Object & Queue Storage** | Azure Storage / Azurite Emulator | Binary contract storage (Blob Storage), resilient job dispatch and retry management (Queue Storage). |
| **Vector Database** | ChromaDB 0.5.20 | Cosine similarity vector indexing, metadata filtering by contract/document, self-healing dimension harmonization. |
| **AI Provider Layer** | Google Gemini (REST API), Ollama, OpenRouter | Active model hosting: `gemma-4-26b-a4b-it` (text generation) and `gemini-embedding-001` (embeddings). |

---

## 4. End-to-End System Workflows

### 4.1 Document Ingestion & Vector Indexing Workflow

```mermaid
sequenceDiagram
    autonumber
    actor User as Legal Administrator
    participant UI as Angular Frontend (:4201)
    participant API as FastAPI Backend (:8080)
    participant Blob as Azure Blob Storage (:10000)
    participant Queue as Azure Queue Storage (:10001)
    participant SQL as SQL Server 2022 (:1433)
    participant Func as Azure Function Processor (:7071)
    participant Embed as Gemini Embedding API
    participant Chroma as ChromaDB (:8000)

    User->>UI: Selects file (PDF/DOCX) & Contract Envelope
    UI->>API: POST /api/v1/documents/upload (multipart/form-data)
    API->>Blob: Upload raw binary to container "legal-contracts-blob"
    API->>SQL: INSERT Documents (status='Uploaded'), ProcessingJobs (status='Queued')
    API->>Queue: Enqueue message {"documentId", "operation":"INGEST", "blob_path"}
    API-->>UI: 202 Accepted {"documentId", "jobId", "status":"Queued"}
    
    Queue->>Func: Dequeue message trigger
    Func->>API: PATCH /api/v1/processing/jobs/{id}/status {"status":"Processing"}
    API->>UI: WebSocket Broadcast {"type":"JOB_UPDATE", "status":"Processing"}
    Func->>Blob: Download raw file bytes
    Func->>Func: Extract text (PdfExtractor) & parse structure (LegalAwareChunker)
    Func->>Embed: POST /v1beta/openai/embeddings (batch chunk texts)
    Embed-->>Func: Return 3072-dimensional embeddings
    Func->>Chroma: Add chunks with metadata to collection "legal_contracts"
    Func->>API: PATCH /api/v1/processing/jobs/{id}/status {"status":"Completed", "page_count":7}
    API->>SQL: UPDATE Documents (status='Completed'), ProcessingJobs (status='Completed')
    API->>UI: WebSocket Broadcast {"type":"JOB_UPDATE", "status":"Completed"}
    UI-->>User: Document table status updates to "Completed"
```

---

### 4.2 Grounded Contract Question Answering Workflow

```mermaid
sequenceDiagram
    autonumber
    actor User as Legal Counsel
    participant UI as Angular Chat Interface
    participant API as FastAPI Backend (:8080)
    participant RAG as EnterpriseRAGService
    participant Embed as Gemini Embedding API
    participant Chroma as ChromaDB (:8000)
    participant LLM as Gemini LLM (gemma-4-26b-a4b-it)
    participant SQL as SQL Server 2022 (:1433)

    User->>UI: Asks question with scoped contract ID
    UI->>API: POST /api/v1/chat/conversations/{id}/messages {"question": "..."}
    API->>RAG: answer_question(question, conversation_id, scoped_contract_ids)
    
    alt Conversational Greeting / General Query ("hii", "what can you do")
        RAG->>LLM: Direct Generation (system prompt, temperature=0.7)
        LLM-->>RAG: Dynamic warm greeting
    else Contractual Query ("What is the late payment interest rate?")
        RAG->>Embed: Embed query string ("gemini-embedding-001")
        Embed-->>RAG: 3072-dim query vector
        RAG->>Chroma: Cosine similarity query (where contract_id IN scopes, top_k=5)
        Chroma-->>RAG: Top 5 chunks with page, section, clause metadata
        RAG->>RAG: ContextBuilder formats structured context
        RAG->>RAG: LegalRAGPromptBuilder v1.1.0 (enforces Amendment Hierarchy)
        RAG->>LLM: Generate Answer (system prompt, context prompt, temperature=0.0)
        LLM-->>RAG: Raw LLM output
        RAG->>RAG: ResponseValidator (strips reasoning bullets, deduplicates sentences)
    end
    
    RAG->>SQL: INSERT Messages (role='assistant'), INSERT RAGSources (chunk_id, doc_name, page, score)
    RAG-->>API: {"answer": "...", "sources": [...]}
    API-->>UI: 200 OK ChatResponse
    UI-->>User: Displays verified answer with inline citations & source inspection drawer
```

---

## 5. Trust Boundaries, Security & Fault Tolerance

```mermaid
flowchart LR
    subgraph Untrusted["Untrusted Public Zone"]
        WebUser["User Browser"]
    end

    subgraph DMZ["Ingress & Perimeter Zone"]
        NginxProxy["Nginx Reverse Proxy (:4201)\n- Port Restriction\n- Header Sanitization"]
    end

    subgraph TrustedApp["Trusted Application Network"]
        APIApp["FastAPI Backend (:8080)\n- RFC 7807 Validation\n- Legal Advice Guardrail Interceptor"]
        FuncWorker["Azure Function Processor (:7071)\n- Input Validation\n- Safe Parsing Engines"]
    end

    subgraph TrustedData["Data Isolation Zone"]
        SQLDB["SQL Server 2022\n- Encrypted Storage\n- Cascading Constraints"]
        Storage["Azurite / Azure Blob & Queue\n- Container-level Isolation"]
        VectorDB["ChromaDB\n- Scoped Query Filters"]
    end

    subgraph ExternalSaaS["External AI Providers"]
        GoogleCloud["Google Generative Language API\n- TLS 1.3 Transport\n- API Key Header Authentication"]
    end

    WebUser -->|HTTPS :4201| NginxProxy
    NginxProxy -->|HTTP Internal| APIApp
    APIApp -->|ODBC Port 1433| SQLDB
    APIApp -->|Blob/Queue 10000-10001| Storage
    FuncWorker -->|Blob/Queue 10000-10001| Storage
    FuncWorker -->|HTTP Port 8000| VectorDB
    APIApp -->|HTTP Port 7071| FuncWorker
    APIApp -->|HTTPS Outbound| GoogleCloud
    FuncWorker -->|HTTPS Outbound| GoogleCloud
```

### 5.1 Fault Tolerance & Self-Healing Matrix

| Failure Mode | Detection Mechanism | Automated Mitigation |
|---|---|---|
| **ChromaDB Dimension Mismatch** | `InvalidCollectionException` / `Dimensionality error` on insert or query | `ProcessorChromaService` catches error, drops the obsolete collection, and recreates it matching the incoming dimension (e.g. 3072). |
| **Model 500 Error from Google API** | HTTP 500 status returned by Generative Language API | `GeminiProvider` detects 500 and attempts automatic fallback across candidate models (`gemini-3.5-flash`, `gemini-flash-latest`). |
| **Document Parsing Crash** | Unhandled exception in PDF/DOCX extractor | Worker catches exception, updates `ProcessingJobs.status = 'Failed'` with stack trace, updates `Documents.status = 'Failed'`, and notifies UI via WebSockets. |
| **Reasoning Model Thought Leakage** | Leading `<think>` tags or bulleted thought traces in raw generation | `ResponseValidator` strips think blocks, parses draft candidates, and deduplicates consecutive duplicate sentences. |
| **Unauthorized Legal Advice Query** | Pattern match on queries asking if clauses are "acceptable", "standard", or "fair" | `MCPGateway` immediately short-circuits the query, returning a safe legal disclaimer without invoking the LLM. |
