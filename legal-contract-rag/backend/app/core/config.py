import os
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Application
    PROJECT_NAME: str = "Enterprise Legal Contract RAG"
    VERSION: str = "2.0.0"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    # SQL Server Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "mssql+pyodbc://sa:YourStrong!Passw0rd@localhost:1433/LegalContractDB?driver=ODBC+Driver+18+for+SQL+Server&Encrypt=no"
    )

    # Azure Blob Storage / Azurite
    AZURE_STORAGE_CONNECTION_STRING: str = os.getenv(
        "AZURE_STORAGE_CONNECTION_STRING",
        "UseDevelopmentStorage=true"
    )
    BLOB_CONTAINER_NAME: str = os.getenv("BLOB_CONTAINER_NAME", "legal-contracts-blob")
    QUEUE_NAME: str = os.getenv("QUEUE_NAME", "legal-document-processing")

    # Document Processor Microservice
    DOCUMENT_PROCESSOR_URL: str = os.getenv("DOCUMENT_PROCESSOR_URL", "http://localhost:7071")

    # ─── Clean Unified AI Configuration ──────────────────────────────────
    # Active Provider: OLLAMA | GEMINI | OPENROUTER (Defaults to OLLAMA)
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", os.getenv("AI_PROVIDER", "OLLAMA")).upper()
    EMBEDDING_PROVIDER: str = os.getenv("EMBEDDING_PROVIDER", os.getenv("LLM_PROVIDER", os.getenv("AI_PROVIDER", "OLLAMA"))).upper()

    # Unified API Key & Models
    API_KEY: Optional[str] = os.getenv("API_KEY", os.getenv("AI_API_KEY", os.getenv("LLM_API_KEY", os.getenv("GEMINI_API_KEY", os.getenv("OPENROUTER_API_KEY", None)))))
    LLM_MODEL: Optional[str] = os.getenv("LLM_MODEL", None)
    EMBEDDING_MODEL: Optional[str] = os.getenv("EMBEDDING_MODEL", None)

    # Ollama Local Configuration Defaults
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "llama3.2")
    OLLAMA_TIMEOUT: float = float(os.getenv("OLLAMA_TIMEOUT", os.getenv("LLM_TIMEOUT", "120")))
    OLLAMA_EMBEDDING_MODEL: str = os.getenv("OLLAMA_EMBEDDING_MODEL", "nomic-embed-text")
    OLLAMA_EMBEDDING_TIMEOUT: float = float(os.getenv("OLLAMA_EMBEDDING_TIMEOUT", "120"))

    # RAG Configuration
    CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", "500"))
    CHUNK_OVERLAP: int = int(os.getenv("CHUNK_OVERLAP", "100"))
    TOP_K: int = int(os.getenv("TOP_K", "5"))

    # Week 4 Hybrid RAG Configuration
    HYBRID_RETRIEVAL_ENABLED: bool = bool(os.getenv("HYBRID_RETRIEVAL_ENABLED", "False").lower() in ("true", "1", "yes"))
    RRF_K: int = int(os.getenv("RRF_K", "60"))
    BM25_TOP_K: int = int(os.getenv("BM25_TOP_K", "10"))
    SEMANTIC_TOP_K: int = int(os.getenv("SEMANTIC_TOP_K", "10"))
    HYBRID_FINAL_TOP_K: int = int(os.getenv("HYBRID_FINAL_TOP_K", "5"))

    class Config:
        case_sensitive = True
        env_file = ".env"
        extra = "ignore"


settings = Settings()
