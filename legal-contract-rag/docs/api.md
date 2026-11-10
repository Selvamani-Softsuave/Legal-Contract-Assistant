# REST & WebSocket API Specification

**Service Name**: Enterprise Legal Contract RAG & Agent Assistant API  
**Base URL**: `http://localhost:8080/api/v1` (Direct API) or `http://localhost:4201/api/v1` (Via Nginx Proxy)  
**API Version**: `2.0.0`  
**Protocol**: HTTP/1.1, WebSocket (RFC 6455)  
**Encoding**: UTF-8, JSON (`application/json`), Multipart Form (`multipart/form-data`)  

---

## 1. Global Architectural Conventions

### 1.1 Cross-Cutting Request Headers

| Header | Type | Required | Description |
|---|---|---|---|
| `X-Correlation-ID` | String (UUIDv4) | Optional | Distributed request correlation identifier. If omitted, the backend generates one automatically and returns it in the response header. |
| `Content-Type` | String | Conditional | `application/json` for JSON payloads, `multipart/form-data` for file uploads. |
| `Accept` | String | Optional | Default `application/json`. |

### 1.2 Error Handling & Problem Details (RFC 7807)

The API strictly implements RFC 7807 Problem Details for all HTTP 4xx and 5xx responses:

```json
{
  "type": "https://api.legalrag.enterprise/errors/validation-error",
  "title": "Validation Error",
  "status": 422,
  "detail": "Field 'contract_number' exceeds maximum length of 100 characters.",
  "instance": "/api/v1/contracts",
  "correlation_id": "a973cb42-2b36-40f4-8a43-0570a049cf1d",
  "invalid_params": [
    {
      "name": "contract_number",
      "reason": "String should have at most 100 characters"
    }
  ]
}
```

#### Standard HTTP Status Codes

| Code | Status | Meaning |
|---|---|---|
| `200` | OK | Request succeeded. Body contains requested data or operation outcome. |
| `201` | Created | Resource successfully created (Contract, Conversation). |
| `202` | Accepted | Asynchronous job queued for background processing (Upload, Reprocess, Purge). |
| `204` | No Content | Deletion operation completed with empty response body. |
| `400` | Bad Request | Syntactically invalid payload or business rule violation. |
| `404` | Not Found | Target entity (Contract, Document, Job, Conversation) does not exist. |
| `422` | Unprocessable Entity | Pydantic validation failure on input fields. |
| `500` | Internal Server Error | Unhandled runtime failure; includes correlation ID for log tracing. |

---

## 2. Contracts API (`/api/v1/contracts`)

Manages contract envelopes that aggregate multiple documents, amendments, and addenda.

### 2.1 Create Contract
- **Method / Path**: `POST /api/v1/contracts`
- **Status**: `201 Created`
- **Request Body**:
```json
{
  "name": "Northwind Logistics MSA Suite",
  "contract_number": "CNT-58C2E303",
  "contract_type": "Master Services Agreement",
  "status": "Draft",
  "effective_date": "2026-01-01T00:00:00Z",
  "expiration_date": "2028-12-31T23:59:59Z",
  "governing_law": "IND",
  "jurisdiction": "New Delhi",
  "description": "Standard Master Services Agreement Suite with Amendments 1 and 2."
}
```
- **Response Body**:
```json
{
  "id": "e84ef743-36a8-49f9-b30f-bf37c651a5da",
  "name": "Northwind Logistics MSA Suite",
  "contract_number": "CNT-58C2E303",
  "contract_type": "Master Services Agreement",
  "status": "Draft",
  "effective_date": "2026-01-01T00:00:00",
  "expiration_date": "2028-12-31T23:59:59",
  "governing_law": "IND",
  "jurisdiction": "New Delhi",
  "version": 1,
  "description": "Standard Master Services Agreement Suite with Amendments 1 and 2.",
  "created_at": "2026-10-09T15:10:37.590000",
  "updated_at": "2026-10-09T15:10:37.590000"
}
```

### 2.2 List Contracts
- **Method / Path**: `GET /api/v1/contracts`
- **Query Parameters**:
  - `skip` (integer, default `0`, min `0`): Pagination offset.
  - `limit` (integer, default `100`, min `1`, max `500`): Maximum records to return.
  - `status` (string, optional): Filter by contract status (`Draft`, `Active`, `Archived`).
- **Response Body**: `List[ContractResponse]`

### 2.3 Get Contract by ID
- **Method / Path**: `GET /api/v1/contracts/{contract_id}`
- **Response**: `200 OK` with single `ContractResponse`. `404 Not Found` if missing.

### 2.4 Update Contract
- **Method / Path**: `PUT /api/v1/contracts/{contract_id}`
- **Request Body**: Partial update containing any mutable fields (`name`, `contract_type`, `status`, `effective_date`, `expiration_date`, `governing_law`, `jurisdiction`, `description`).
- **Response**: `200 OK` with updated `ContractResponse`.

### 2.5 Delete Contract
- **Method / Path**: `DELETE /api/v1/contracts/{contract_id}`
- **Status**: `204 No Content`
- **Description**: Soft-deletes or cascade-removes contract and associated document records.

---

## 3. Documents API (`/api/v1/documents`)

Handles file upload to Azure Blob Storage, asynchronous queue dispatch to the Document Processor microservice, vector purging, and document downloads.

### 3.1 Upload Document
- **Method / Path**: `POST /api/v1/documents/upload`
- **Content-Type**: `multipart/form-data`
- **Form Fields**:
  - `contract_id` (string, UUIDv4, required): Parent contract ID.
  - `file` (binary file, required): PDF, DOCX, or TXT file.
- **Status**: `202 Accepted`
- **Response Body**:
```json
{
  "documentId": "7a82f777-86fd-483c-a132-244cbd0cb79e",
  "contractId": "e84ef743-36a8-49f9-b30f-bf37c651a5da",
  "fileName": "MSA-2026-014_Northwind_Master_Services_Agreement.pdf",
  "fileSize": 130650,
  "status": "Queued",
  "jobId": "f8643e5b-b352-4bb4-b545-75a445ac5266",
  "correlationId": "48f8ccc0-5579-4714-8e01-542cd70e1ee7",
  "message": "Document uploaded successfully and queued for processing."
}
```

### 3.2 List All Documents
- **Method / Path**: `GET /api/v1/documents?limit=100`
- **Response**: `List[DocumentResponse]`

### 3.3 List Contract Documents
- **Method / Path**: `GET /api/v1/documents/contract/{contract_id}`
- **Response**: `List[DocumentResponse]` for the scoped contract.

### 3.4 Get Document Metadata
- **Method / Path**: `GET /api/v1/documents/{document_id}`
- **Response Body**:
```json
{
  "id": "7a82f777-86fd-483c-a132-244cbd0cb79e",
  "contract_id": "e84ef743-36a8-49f9-b30f-bf37c651a5da",
  "contract_name": "Northwind Logistics MSA Suite",
  "file_name": "MSA-2026-014_Northwind_Master_Services_Agreement.pdf",
  "file_size": 130650,
  "file_type": "pdf",
  "blob_path": "legal-contracts-blob/contracts/e84ef743-36a8-49f9-b30f-bf37c651a5da/7a82f777-86fd-483c-a132-244cbd0cb79e.pdf",
  "page_count": 7,
  "status": "Completed",
  "created_at": "2026-10-09T15:14:17.107000",
  "updated_at": "2026-11-06T06:05:35.113000"
}
```

### 3.5 Download Original File
- **Method / Path**: `GET /api/v1/documents/{document_id}/download`
- **Response**: Binary stream (`application/octet-stream`) with `Content-Disposition: attachment; filename="<original_name>"`.

### 3.6 Reprocess Document
- **Method / Path**: `POST /api/v1/documents/{document_id}/reprocess`
- **Status**: `202 Accepted`
- **Description**: Purges existing vector embeddings in ChromaDB, downloads the original blob, re-extracts clauses, re-embeds using the active model, and pushes new chunks into ChromaDB.

### 3.7 Delete Document & Purge Vectors
- **Method / Path**: `DELETE /api/v1/documents/{document_id}`
- **Status**: `202 Accepted`
- **Description**: Deletes document metadata and enqueues an asynchronous `DELETE_INDEX` background task to purge chunks from ChromaDB and delete blob bytes from storage.

---

## 4. Processing Jobs API (`/api/v1/processing`)

Allows tracking and updating asynchronous document pipeline jobs.

### 4.1 Get Job Status
- **Method / Path**: `GET /api/v1/processing/jobs/{job_id}`
- **Response Body**:
```json
{
  "id": "f8643e5b-b352-4bb4-b545-75a445ac5266",
  "document_id": "7a82f777-86fd-483c-a132-244cbd0cb79e",
  "operation": "REPROCESS",
  "status": "Completed",
  "correlation_id": "48f8ccc0-5579-4714-8e01-542cd70e1ee7",
  "started_at": "2026-11-06T06:58:35.100000",
  "completed_at": "2026-11-06T06:58:47.300000",
  "error_message": null,
  "retry_count": 0
}
```

### 4.2 Update Job Status (Internal / Microservice Webhook)
- **Method / Path**: `PATCH /api/v1/processing/jobs/{job_id}/status`
- **Request Body**:
```json
{
  "status": "Completed",
  "document_id": "7a82f777-86fd-483c-a132-244cbd0cb79e",
  "page_count": 7,
  "chunk_count": 14,
  "error_message": null
}
```
- **Side Effect**: Updates SQL Server job and document records, then broadcasts a real-time `JOB_UPDATE` event via WebSockets to all connected UI clients.

---

## 5. Chat & Grounded RAG API (`/api/v1/chat`)

Primary conversational interface for legal question-answering and contract analysis.

### 5.1 Create Conversation
- **Method / Path**: `POST /api/v1/chat/conversations`
- **Status**: `201 Created`
- **Request Body**:
```json
{
  "title": "Northwind Late Payment Review",
  "scoped_contract_ids": ["e84ef743-36a8-49f9-b30f-bf37c651a5da"]
}
```
- **Response Body**:
```json
{
  "id": "83dfecff-669d-43e6-ae0c-edac2f6613c8",
  "title": "Northwind Late Payment Review",
  "scoped_contract_ids": "[\"e84ef743-36a8-49f9-b30f-bf37c651a5da\"]",
  "created_at": "2026-11-06T06:54:52.120000",
  "updated_at": "2026-11-06T06:54:52.120000"
}
```

### 5.2 List Conversations
- **Method / Path**: `GET /api/v1/chat/conversations`
- **Response**: `List[ConversationResponse]` ordered by `updated_at` descending.

### 5.3 Get Conversation Message History
- **Method / Path**: `GET /api/v1/chat/conversations/{conversation_id}/messages`
- **Response**: `List[MessageResponse]` including citations and source chunks for assistant responses.

### 5.4 Send Message & Generate Grounded RAG Response
- **Method / Path**: `POST /api/v1/chat/conversations/{conversation_id}/messages`
- **Request Body**:
```json
{
  "question": "What is the late payment interest rate under the Northwind Master Services Agreement?",
  "scoped_contract_ids": ["e84ef743-36a8-49f9-b30f-bf37c651a5da"]
}
```
- **Processing Logic**:
  1. **Conversational Intent Check**: If the question is a greeting (`hi`, `hii`, `heyy`) or identity question (`who are you`, `what is your name`), it routes directly to dynamic LLM response generation with temperature `0.7` without failing vector search.
  2. **Vector Similarity Retrieval**: Generates query embedding with the active embedding provider and queries ChromaDB with contract scoping filters.
  3. **Standardized Prompt Assembly**: Evaluates amendment hierarchy and builds the context.
  4. **Active LLM Dispatch**: Calls the active provider (Gemini, Ollama, OpenRouter).
  5. **Response Validation**: Normalizes formatting, strips thinking traces, and formats citations.
- **Response Body**:
```json
{
  "message_id": "2195f171-8bc6-464a-9ef1-3444ca76d90e",
  "answer": "Under the Northwind Master Services Agreement, any undisputed amount not paid when due shall accrue interest at a rate of one and one-half percent (1.5%) per month, or the maximum rate permitted by applicable law, whichever is lower (MSA-2026-014_Northwind_Master_Services_Agreement.pdf, Section 3.4).",
  "sources": [
    {
      "chunk_id": "7a82f777-86fd-483c-a132-244cbd0cb79e_chunk_2",
      "document_name": "MSA-2026-014_Northwind_Master_Services_Agreement.pdf",
      "page_number": 3,
      "section": "3.4",
      "clause": "Late Payment",
      "similarity_score": 0.884,
      "text_content": "Section 3.4 Late Payment. Any undisputed amount not paid when due shall bear interest at 1.5% per month or the maximum legal rate..."
    }
  ],
  "created_at": "2026-11-06T07:01:45.300000"
}
```

---

## 6. WebSocket Real-Time Events (`/api/v1/ws/events`)

Bi-directional WebSocket connection for streaming asynchronous processing job updates to the UI.

- **WebSocket URL**: `ws://localhost:8080/api/v1/ws/events` (Direct) or `ws://localhost:4201/ws/` (Proxy)
- **Protocol**: Standard WebSocket (WSS in production)
- **Broadcast Message Structure**:
```json
{
  "type": "JOB_UPDATE",
  "document_id": "7a82f777-86fd-483c-a132-244cbd0cb79e",
  "status": "Processing",
  "job_id": "f8643e5b-b352-4bb4-b545-75a445ac5266",
  "page_count": 7
}
```

---

## 7. Agent & MCP APIs (`/api/v1/agent` & `/api/v1/mcp`)

### 7.1 Agent Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/v1/agent/tools` | Discovers the 3 typed single-job tools available to the ReAct agent (`get_clause`, `get_definitions`, `get_precedence`). |
| `GET` | `/api/v1/agent/race-dataset` | Retrieves the 10 curated test cases for the ReAct vs Fixed Workflow benchmark. |
| `POST` | `/api/v1/agent/query` | Executes an iterative ReAct reasoning loop with dynamic tool dispatch and budget tracking. |
| `POST` | `/api/v1/agent/run-race` | Executes the 10-question race comparing ReAct Agent against Fixed Workflow. |
| `GET` | `/api/v1/agent/trajectory-eval` | Runs step-by-step trajectory evaluation across the golden evaluation dataset. |
| `POST` | `/api/v1/agent/mitigation-benchmark` | Evaluates prompt injection attack mitigations and calculates security tax. |
| `POST` | `/api/v1/agent/injection-attack` | Tests deliberate adversarial prompt injection against agent safety boundaries. |
| `POST` | `/api/v1/agent/w10-race` | Coordinates the 3-arm architectural race (ReAct vs Fixed Workflow vs Multi-Agent). |
| `POST` | `/api/v1/agent/w10-inject-failure` | Tests resilience by injecting worker timeouts, corrupted outputs, or process drops. |
| `GET` | `/api/v1/agent/w10-handoff-logs` | Retrieves structured A2A (agent-to-agent) handoff audit logs. |
| `GET` | `/api/v1/agent/w10-agent-card` | Returns the A2A Agent Card defining capabilities and operational SLAs. |

### 7.2 Model Context Protocol (MCP) Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/v1/mcp/discovery` | Dynamically discovers registered MCP tools across all enabled MCP servers via JSON-RPC 2.0. |
| `POST` | `/api/v1/mcp/query` | Runs the decoupled `MCPAgentHost` against dynamically discovered MCP servers. |
| `POST` | `/api/v1/mcp/call-tool` | Directly calls an MCP tool on a specified server via JSON-RPC 2.0 dispatch. |
| `GET` | `/api/v1/mcp/wire-trace` | Returns real-time JSON-RPC 2.0 wire traces (request, response, latency, payloads). |
| `DELETE` | `/api/v1/mcp/wire-trace` | Clears stored wire traces in memory. |
| `GET` | `/api/v1/mcp/audit-logs` | Returns structured audit events for tool invocations and legal guardrail intercepts. |
| `GET` | `/api/v1/mcp/error-demo` | Demonstrates graceful error propagation (tool error, relocation, protocol failure). |

---

## 8. Observability & Health Endpoints

### 8.1 Health Check (`/health`)
- **Method / Path**: `GET /health`
- **Response Body**:
```json
{
  "status": "healthy",
  "environment": "development",
  "version": "2.0.0",
  "active_llm": {
    "status": "healthy",
    "provider": "gemini",
    "model": "gemma-4-26b-a4b-it"
  }
}
```

### 8.2 Observability Tracing & Cost Metrics

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/v1/observability/logs` | Fetches historical request traces with token counts, latencies, and tool calls. |
| `GET` | `/api/v1/observability/traces/{trace_id}` | Retrieves a single end-to-end distributed trace by correlation ID. |
| `POST` | `/api/v1/observability/drill` | Runs a synthetic support drill verifying observability and root-cause attribution. |
| `GET` | `/api/v1/observability/canary-config` | Retrieves the active canary routing deployment configuration. |
| `POST` | `/api/v1/observability/canary-config` | Updates canary traffic weights (e.g., 90% production / 10% canary). |
| `GET` | `/api/v1/observability/cost-summary` | Aggregates token consumption, estimated monetary cost, and cost-by-stage. |

