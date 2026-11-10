# Deployment & Infrastructure Configuration Guide

**Environment Scope**: Development, Staging, Enterprise Production  
**Containerization**: Docker & Docker Compose (`compose.yaml` / `docker-compose.yml`)  
**Container Count**: 7 Dedicated Microservices  
**Primary Ingress**: `http://localhost:4201` (Frontend UI), `http://localhost:8080` (Backend API)  

---

## 1. Container Infrastructure Topology

The system deploys as a cohesive multi-container Docker Compose stack:

```mermaid
graph TD
    Client[Browser Client] -->|Port 4201| Frontend[legal_frontend\nAngular 19 + Nginx]
    
    subgraph AppNetwork["Docker Network (legal-contract-rag_default)"]
        Frontend -->|Reverse Proxy /api/| Backend[legal_backend\nFastAPI :8000 -> 8080]
        Frontend -->|Reverse Proxy /ws/| Backend
        
        Backend -->|Metadata Queries| SQL[legal_sqlserver\nSQL Server 2022 :1433]
        Backend -->|Blob Upload & Queue Enqueue| Azurite[legal_azurite\nBlob :10000 | Queue :10001]
        
        Queue[(Azure Queue Storage)] -->|Queue Trigger| Processor[legal_processor\nAzure Functions Python :80 -> 7071]
        Azurite -.-> Queue
        
        Processor -->|Download Blobs| Azurite
        Processor -->|Extract & Chunk| Processor
        Processor -->|Generate Embeddings| AIProvider[AI Provider APIs\nGemini / Ollama / OpenRouter]
        Processor -->|Store Vectors & Metadata| Chroma[legal_chromadb\nChromaDB 0.5.20 :8000]
        
        Backend -->|Dense Similarity Search| Processor
        Backend -->|LLM Chat & RAG Generation| AIProvider
        Backend -->|Status Broadcasts| Frontend
    end
```

### 1.1 Container Specification Summary

| Container Name | Base Image | Host Port | Container Port | Purpose |
|---|---|---|---|---|
| `legal_frontend` | `node:20-alpine` $\to$ `nginx:alpine` | **`4201`** | `80` | Angular 19 SPA, static assets, reverse proxy for `/api/` and `/ws/`. |
| `legal_backend` | `python:3.11-slim` | **`8080`** | `8000` | FastAPI REST API, SQLAlchemy ORM, Alembic migrations, RAG orchestration. |
| `legal_processor` | `mcr.microsoft.com/azure-functions/python:4-python3.11` | **`7071`** | `80` | Background document parser, `LegalAwareChunker`, embedding worker. |
| `legal_chromadb` | `chromadb/chroma:0.5.20` | **`8000`** | `8000` | Vector database for contract chunk embeddings. |
| `legal_sqlserver` | `mcr.microsoft.com/mssql/server:2022-latest` | **`1433`** | `1433` | Relational database storing contracts, documents, jobs, and chat messages. |
| `legal_azurite` | `mcr.microsoft.com/azure-storage/azurite:latest` | **`10000-10002`** | `10000-10002` | Local storage emulator for Azure Blob (10000), Queue (10001), Table (10002). |
| `legal_ollama` | `ollama/ollama:latest` | **`11434`** | `11434` | Optional local LLM and embedding service for 100% offline deployment. |

---

## 2. Environment Variables & Configuration Matrix

Configuration is centralized in the root `.env` file (copied into containers via Docker Compose).

### 2.1 Core Platform Configuration

| Variable | Type | Default | Description |
|---|---|---|---|
| `ENVIRONMENT` | String | `development` | Runtime environment (`development`, `staging`, `production`). |
| `LOG_LEVEL` | String | `INFO` | Logging verbosity (`DEBUG`, `INFO`, `WARNING`, `ERROR`). |
| `PROJECT_NAME` | String | `Enterprise Legal Contract RAG` | System identifier in logs and OpenAPI docs. |
| `VERSION` | String | `2.0.0` | API semantic version. |

### 2.2 Relational Database & Storage

| Variable | Service Scope | Default Value | Notes |
|---|---|---|---|
| `DATABASE_URL` | Backend, Processor | `mssql+pyodbc://sa:LegalRAG_Password2026!@sqlserver:1433/LegalContractRAG?driver=ODBC+Driver+17+for+SQL+Server` | Connection string for SQL Server 2022. |
| `MSSQL_SA_PASSWORD` | SQL Server | `LegalRAG_Password2026!` | SA password. Must satisfy SQL Server complexity requirements. |
| `AZURE_STORAGE_CONNECTION_STRING` | Backend, Processor | `DefaultEndpointsProtocol=http;AccountName=devstoreaccount1;...` | Azurite connection string. In production, replace with Azure Storage Account key. |
| `BLOB_CONTAINER_NAME` | Backend, Processor | `legal-contracts-blob` | Target blob storage container. |
| `QUEUE_NAME` | Backend, Processor | `legal-document-processing` | Queue name for background processing jobs. |

### 2.3 Dynamic AI Provider Configuration

The platform supports hot-switching between AI providers via environment variables:

| Variable | Allowed Values | Active Production Value | Description |
|---|---|---|---|
| `AI_PROVIDER` | `GEMINI`, `OLLAMA`, `OPENROUTER`, `OPENAI` | **`GEMINI`** | Global AI provider selection. |
| `LLM_PROVIDER` | `GEMINI`, `OLLAMA`, `OPENROUTER`, `OPENAI` | **`GEMINI`** | LLM text generation provider. |
| `EMBEDDING_PROVIDER`| `GEMINI`, `OLLAMA`, `OPENROUTER`, `OPENAI` | **`GEMINI`** | Vector embedding generation provider. |
| `AI_API_KEY` / `API_KEY` | String | `AQ.Ab8RN...` | Shared API key used for LLM and Embedding API calls. |
| `LLM_MODEL` | String | `gemma-4-26b-a4b-it` | Active LLM model name. |
| `EMBEDDING_MODEL` | String | `gemini-embedding-001` | Active embedding model name. |
| `TOP_K` | Integer | `5` | Number of context chunks retrieved for RAG synthesis. |
| `HYBRID_SEARCH_ENABLED` | Boolean | `False` | Toggle BM25 + Dense vector Reciprocal Rank Fusion. |

---

## 3. Step-by-Step Deployment Instructions

### 3.1 Prerequisites
- **Operating System**: Windows 10/11, macOS, or Linux.
- **Docker Engine & Docker Compose**: Docker Desktop 4.25+ or Docker Engine 24.0+.
- **Hardware Minimums**: 4 CPU cores, 8 GB RAM, 20 GB free disk space.
- **Network**: Port access for `4201`, `8080`, `7071`, `8000`, `1433`, `10000`, `10001`.

### 3.2 Automated Docker Compose Deployment

```powershell
# 1. Clone repository
git clone https://github.com/your-org/legal-contract-rag.git
cd legal-contract-rag

# 2. Configure Environment Secrets
# Ensure .env contains your active AI_API_KEY and AI_PROVIDER="GEMINI"

# 3. Build and launch all 7 containers in detached mode
docker-compose up -d --build

# 4. Monitor startup and database migration logs
docker-compose logs -f backend
```

Once `Application startup complete.` appears in the backend logs, access:
- **Web User Interface**: [`http://localhost:4201`](http://localhost:4201)
- **FastAPI Interactive Docs**: [`http://localhost:8080/docs`](http://localhost:8080/docs)
- **System Health Endpoint**: [`http://localhost:8080/health`](http://localhost:8080/health)

### 3.3 Ingesting the Baseline Contract Corpus

To seed the database with the Northwind Logistics Master Services Agreement Suite:

```powershell
# Execute the corpus ingestion script against the frontend proxy
python scripts/ingest_shared_corpus_to_ui.py
```

This uploads the 6 core contractual documents (`MSA-2026-014`, `AMD-2026-014-01`, `AMD-2026-014-02`, `SCH-2026-014`, `MSA-2026-022`, `NDA-2026-007`), triggers the Azure Function queue processor, and stores 3072-dimensional embeddings in ChromaDB.

---

## 4. Local Development (Non-Containerized)

### 4.1 Backend API (FastAPI)
```powershell
# Create and activate virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r backend/requirements.txt

# Run migrations
alembic upgrade head

# Start FastAPI development server
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 4.2 Document Processor (Azure Functions)
```powershell
cd processor
pip install -r requirements.txt
func start --port 7071
```

### 4.3 Frontend Web Application (Angular 19)
```powershell
cd frontend
npm install

# Start local dev server on port 4201 with proxy to backend
npm start
# Equivalent to: ng serve --port 4201 --proxy-config proxy.conf.json
```

---

## 5. Operations & Troubleshooting Playbook

### 5.1 Frontend Port Conflict (`Port 4200 is already in use`)
- **Root Cause**: Another service (or an earlier development server) occupies port `4200`.
- **Solution**: The application is permanently configured to port `4201` in:
  - `docker-compose.yml` (`4201:80`)
  - `frontend/angular.json` (`"port": 4201`)
  - `frontend/package.json` (`--port 4201`)
- Verify running instances: `Get-Process -Id (Get-NetTCPConnection -LocalPort 4201).OwningProcess`.

### 5.2 ChromaDB Dimension Mismatch (`Expected dimension 768, got 3072`)
- **Root Cause**: Switching between embedding providers (e.g., from Ollama's `nomic-embed-text` with 768 dimensions to Gemini's `gemini-embedding-001` with 3072 dimensions) causes ChromaDB to reject new embeddings.
- **Solution**: The processor includes automatic self-healing logic in [`processor/services/chroma_service.py`](file:///processor/services/chroma_service.py). To trigger an immediate rebuild:
  1. Trigger document re-processing via `POST /api/v1/documents/{document_id}/reprocess`.
  2. The processor drops the old collection and recreates it with `dimension: 3072`.

### 5.3 SQL Server Container Fails on Startup
- **Root Cause**: Docker container crashes if `MSSQL_SA_PASSWORD` does not meet Microsoft SQL Server complexity rules (minimum 8 characters, uppercase, lowercase, numbers, special characters).
- **Solution**: Keep password set to `LegalRAG_Password2026!` in `.env` and `docker-compose.yml`.

### 5.4 Document Processor Skips Uploaded Documents
- **Root Cause**: Queue trigger payload contains operation name not handled by processor.
- **Solution**: Verify [`processor/function_app.py`](file:///processor/function_app.py) handles `["PROCESS", "REPROCESS", "INGEST"]`. All three are supported in production.

### 5.5 Checking System Logs

```powershell
# View real-time logs for backend
docker logs -f legal_backend --tail 50

# View real-time logs for document processor
docker logs -f legal_processor --tail 50

# View real-time logs for ChromaDB
docker logs -f legal_chromadb --tail 50
```

