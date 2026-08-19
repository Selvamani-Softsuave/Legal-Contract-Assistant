# Enterprise Legal Contract RAG System

An enterprise-ready, modular **Retrieval-Augmented Generation (RAG)** platform for legal contract ingestion, legal-aware clause chunking, vector search, and grounded question answering with source citations.

---

## 🏛️ Architecture Overview

```mermaid
graph TD
    UI[Angular Frontend :4200] -->|REST API| API[FastAPI Backend :8080]
    API -->|Metadata & History| SQL[(SQL Server :1433)]
    API -->|Blob/Queue Storage| Blob[(Azurite :10000-10001)]
    API -->|Enqueue Jobs| Queue[(Azure Queue)]
    Queue -->|Queue Trigger| Proc[Azure Function Processor :7071]
    Proc -->|Download Blob| Blob
    Proc -->|Extract & Chunk| Engine[LegalAwareChunker]
    Engine -->|Embeddings| AI[AI Provider\nOllama / OpenRouter / Gemini / ...]
    AI -->|Store Vectors| Chroma[(ChromaDB :8000)]
    API -->|RAG Search| Chroma
    API -->|LLM Chat| AI
```

| Service | Technology | Port |
|---|---|---|
| Frontend | Angular 17+ | 4200 |
| Backend API | FastAPI + SQLAlchemy | 8080 |
| Document Processor | Azure Functions (Python) | 7071 |
| Database | SQL Server 2022 | 1433 |
| Blob & Queue Storage | Azurite (local Azure emulator) | 10000-10002 |
| Vector Store | ChromaDB 0.4.24 | 8000 |
| AI (local option) | Ollama | 11434 |

---

## 🤖 Dynamic AI Provider Configuration

The application supports **any OpenAI-compatible LLM and embedding API** without code changes. Switch providers by editing a single `.env` variable.

### Supported Providers

| `AI_PROVIDER` | LLM Chat | Embeddings | Free? |
|---|---|---|---|
| `OLLAMA` | Local Ollama (`/api/generate`) | Local Ollama (`/api/embed`) | ✅ Free (local) |
| `OPENROUTER` | 100+ models | `jinaeu/jina-embeddings-v2-base-en` | ✅ Free tier |
| `OPENAI` | `gpt-4o-mini` | `text-embedding-3-small` | 💳 Paid |
| `GEMINI` | `gemini-1.5-flash` | `text-embedding-004` | ✅ Free tier |
| `GROQ` | `llama-3.1-8b-instant` | *(use OpenRouter for embeddings)* | ✅ Free tier |
| `DEEPSEEK` | `deepseek-chat` | *(use OpenRouter for embeddings)* | 💲 Very cheap |
| `CUSTOM` | Any OpenAI-compatible URL | Any OpenAI-compatible URL | Varies |

### Minimal Configuration

Edit **one block** in your `.env` file (root or `backend/.env`):

```env
# Option 1 — Local Ollama (no internet, free, requires Docker or local install)
AI_PROVIDER=OLLAMA

# Option 2 — OpenRouter (free tier models available)
AI_PROVIDER=OPENROUTER
AI_API_KEY=sk-or-v1-your-key-here

# Option 3 — Google Gemini (free tier)
AI_PROVIDER=GEMINI
AI_API_KEY=AIzaSy-your-gemini-key-here

# Option 4 — Completely custom provider
AI_PROVIDER=CUSTOM
LLM_BASE_URL=https://your-provider.com/v1
LLM_API_KEY=your-api-key
LLM_MODEL=your-model-name
EMBEDDING_BASE_URL=https://your-provider.com/v1
EMBEDDING_MODEL=your-embedding-model
```

> **Model overrides:**  Use `LLM_MODEL` and `EMBEDDING_MODEL` to override any provider's default model without changing code.

---

## 🚀 Local Development Setup

### Prerequisites

- Python **3.11** (required by Azure Functions Core Tools)
- Node.js 18+ and Angular CLI: `npm install -g @angular/cli`
- Azure Functions Core Tools v4: [Install guide](https://learn.microsoft.com/en-us/azure/azure-functions/functions-run-local)
- Docker & Docker Compose (for infrastructure services)
- ODBC Driver 17 for SQL Server

### Step 1 — Start Infrastructure Services (Docker)

```powershell
docker-compose up -d sqlserver azurite chromadb
```

This starts SQL Server, Azurite (Blob + Queue), and ChromaDB — **without** building the backend or processor images.

### Step 2 — Initialize the Database (first time only)

```powershell
cd "E:\Selvamani\Learning\AI Learning\legal-contract-rag"
python backend/scripts/init_db.py
```

This creates the `LegalContractRAG` database and runs all Alembic migrations to set up tables.

### Step 3 — Configure AI Provider

Edit `backend/.env` and `processor/local.settings.json` with your chosen provider:

```env
# backend/.env
AI_PROVIDER=OPENROUTER
AI_API_KEY=sk-or-v1-your-key-here
```

```json
// processor/local.settings.json → "Values" block
"AI_PROVIDER": "OPENROUTER",
"AI_API_KEY": "sk-or-v1-your-key-here"
```

### Step 4 — Start the Backend API

```powershell
cd "E:\Selvamani\Learning\AI Learning\legal-contract-rag"
uvicorn backend.app.main:app --reload --port 8080
```

API Docs: [http://localhost:8080/docs](http://localhost:8080/docs)

### Step 5 — Start the Document Processor

```powershell
cd processor

# Install dependencies (first time or after requirements change)
pip install -r requirements.txt

func start
```

> ⚠️  Azure Functions Core Tools uses Python **3.11** internally. Your `venv` should be created with Python 3.11.

### Step 6 — Start the Angular Frontend

```powershell
cd frontend
npm install
npm start
```

Frontend: [http://localhost:4200](http://localhost:4200)

---

## 🐳 Full Docker Deployment

### Step 1 — Configure Root `.env`

The root `.env` is the **single source of truth** for `docker-compose`. Both the backend and processor containers read AI provider config from it via `${AI_PROVIDER}` variable substitution:

```env
# .env (project root)
AI_PROVIDER=OPENROUTER
AI_API_KEY=sk-or-v1-your-key-here
EMBEDDING_MODEL=jinaeu/jina-embeddings-v2-base-en
```

### Step 2 — Build and Start All Services

```powershell
docker-compose up --build -d
```

The **backend container automatically**:
1. ⏳ Waits for SQL Server to be ready
2. 🗄️ Creates the `LegalContractRAG` database if missing
3. 📋 Runs `alembic upgrade head` to create/update all tables
4. 🚀 Starts the API server

### Exposed Endpoints

| Service | URL |
|---|---|
| Frontend | [http://localhost:4200](http://localhost:4200) |
| Backend API Docs | [http://localhost:8080/docs](http://localhost:8080/docs) |
| Document Processor | [http://localhost:7071](http://localhost:7071) |
| ChromaDB | [http://localhost:8000](http://localhost:8000) |
| Azurite Blob | [http://localhost:10000](http://localhost:10000) |
| SQL Server | `localhost:1433` |

### Using Local Ollama in Docker

If `AI_PROVIDER=OLLAMA`, pull models into your Ollama container before processing:

```powershell
docker exec -it legal_ollama ollama pull llama3.2
docker exec -it legal_ollama ollama pull nomic-embed-text
```

---

## 📁 Project Structure

```
legal-contract-rag/
├── .env                      # Root env — read by docker-compose
├── docker-compose.yml
├── backend/
│   ├── .env                  # Backend local dev env
│   ├── Dockerfile
│   ├── scripts/
│   │   ├── init_db.py        # Local DB init (run once)
│   │   └── start.sh          # Docker entrypoint (auto-init DB + migrate)
│   ├── app/
│   │   ├── core/config.py    # All settings
│   │   ├── services/
│   │   │   ├── embedding_service.py   # Dynamic multi-provider embeddings
│   │   │   └── ollama_service.py      # Dynamic multi-provider LLM
│   │   └── ...
│   └── alembic/              # Database migration scripts
├── processor/
│   ├── local.settings.json   # Processor local dev env (gitignored)
│   ├── requirements.txt
│   ├── function_app.py       # Azure Function entry point
│   └── services/
│       ├── embedding_service.py   # Dynamic multi-provider embeddings
│       ├── chroma_service.py      # ChromaDB (HTTP or persistent)
│       └── ...
└── frontend/                 # Angular 17+ application
```

---

## 🧪 Running Tests

```powershell
cd "E:\Selvamani\Learning\AI Learning\legal-contract-rag"
pytest tests/ -v
```

---

## ⚙️ Key Environment Variables Reference

| Variable | Description | Example |
|---|---|---|
| `AI_PROVIDER` | Active AI provider | `OLLAMA`, `OPENROUTER`, `GEMINI` |
| `AI_API_KEY` | Shared API key for LLM + embeddings | `sk-or-v1-...` |
| `LLM_MODEL` | Override LLM model name | `meta-llama/llama-3.1-8b-instruct:free` |
| `EMBEDDING_MODEL` | Override embedding model name | `jinaeu/jina-embeddings-v2-base-en` |
| `LLM_BASE_URL` | Override LLM endpoint (any provider) | `https://api.groq.com/openai/v1` |
| `LLM_API_KEY` | Override LLM-specific key | *(optional, falls back to AI_API_KEY)* |
| `EMBEDDING_BASE_URL` | Override embedding endpoint | `https://openrouter.ai/api/v1` |
| `EMBEDDING_API_KEY` | Override embedding-specific key | *(optional, falls back to AI_API_KEY)* |
| `OLLAMA_BASE_URL` | Local Ollama URL | `http://localhost:11434` |
| `DATABASE_URL` | SQL Server connection string | `mssql+pyodbc://sa:pass@host/db?...` |
| `CHROMA_HOST` | ChromaDB host (HTTP mode) | `127.0.0.1` or `chromadb` (Docker) |
| `CHROMA_PORT` | ChromaDB port | `8000` |


---

## 🏛️ Architecture Overview

The system is decoupled into three core tiers:

1. **Angular 17+ Frontend (`frontend/`)**: Modern UI built with Angular Material, featuring contract lifecycle management, asynchronous document upload progress tracking, interactive chat, and a slide-out Citation Drawer.
2. **FastAPI Backend (`backend/`)**: Relational metadata API managing contracts, documents, processing job queues, conversation history, and persisted citation sources (`RAGSources`) using SQL Server and SQLAlchemy.
3. **Document Processor Azure Functions (`processor/`)**: Isolated microservice handling document extraction (PDF, DOCX, TXT), `LegalAwareChunker` structural clause parsing (Articles, Sections, Clauses), embedding generation (SentenceTransformers / Ollama), and isolated ChromaDB vector indexing.

```mermaid
graph TD
    UI[Angular 17 Frontend] -->|REST API| API[FastAPI Backend]
    API -->|Metadata & History| SQL[(SQL Server)]
    API -->|Blob Storage| Blob[(Azurite / Azure Blob)]
    API -->|Enqueue Jobs| Queue[(Azure Queue)]
    Queue -->|Queue Trigger| Proc[Document Processor Azure Function]
    Proc -->|Download File| Blob
    Proc -->|Extract & Legal Chunk| Engine[Legal-Aware Engine]
    Engine -->|Generate Embeddings| Embed[SentenceTransformers / Ollama]
    Embed -->|Store Vectors| Chroma[(ChromaDB)]
    API -->|Vector Search API| Proc
```

---

## 🚀 Key Features

* **Asynchronous Queue Ingestion**: Document uploads return immediate `202 Accepted` responses. Ingestion runs asynchronously via Azure Queue (`legal-document-processing`).
* **Legal-Aware Chunking (`LegalAwareChunker`)**: Respects legal hierarchy boundaries (Articles, Sections, Subsections, Clauses, Headings) without breaking contractual clauses across chunks.
* **Vector Store Isolation**: ChromaDB is kept strictly internal to the Document Processor microservice and accessed exclusively via internal REST APIs (`/api/vector/search`, `/api/vector/delete`).
* **Relational Citation Persistence**: User questions, assistant answers, and detailed chunk citations (Document Name, Page, Section, Clause, Relevance Score) are stored in SQL Server.
* **Resilient Infrastructure**: Full Azurite (Blob & Queue) integration with seamless local disk and logging fallbacks.

---

## 🛠️ Local Development & Quickstart

### Prerequisites
* Python 3.10+
* Node.js 18+ and Angular CLI (`npm install -g @angular/cli`)
* Docker & Docker Compose (optional for containerized deployment)

### 1. Database & Migrations Setup
```bash
cd backend
pip install -r requirements.txt
alembic upgrade head
```

### 2. Run Backend API Server
```bash
uvicorn backend.app.main:app --reload --port 8000
```
Swagger API Documentation: [http://localhost:8000/docs](http://localhost:8000/docs)

### 3. Run Document Processor Azure Function
```bash
cd processor
pip install -r requirements.txt
func start
```

### 4. Run Angular Frontend
```bash
cd frontend
npm install
npm start
```
Frontend Web UI: [http://localhost:4200](http://localhost:4200)

---

## 🐳 Containerized Deployment (Docker Compose)

Launch the complete 7-container enterprise stack (SQL Server, Azurite, ChromaDB, Ollama, Backend, Processor, Frontend) with a single command:

```bash
docker-compose up --build -d
```

Services exposed:
* **Frontend UI**: `http://localhost`
* **FastAPI Backend**: `http://localhost:8080/docs`
* **Document Processor Function**: `http://localhost:7071`
* **SQL Server**: `localhost:1433`
* **Azurite Emulator**: `localhost:10000` (Blob), `10001` (Queue)

---

## 🧪 Testing Strategy

Run the automated pytest test suite covering domain models, legal extractors, chunkers, and FastAPI endpoint routes:

```bash
pytest tests/ -v
```
