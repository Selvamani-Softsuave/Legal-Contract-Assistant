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

    # Dynamic AI Provider Configuration (OLLAMA, OPENAI, OPENROUTER, GEMINI, GROQ, DEEPSEEK, CUSTOM)
    AI_PROVIDER: str = os.getenv("AI_PROVIDER", "OLLAMA")
    LLM_PROVIDER: Optional[str] = os.getenv("LLM_PROVIDER", None)
    EMBEDDING_PROVIDER: Optional[str] = os.getenv("EMBEDDING_PROVIDER", None)

    # Base URLs & Keys (Optional overrides)
    LLM_BASE_URL: Optional[str] = os.getenv("LLM_BASE_URL", None)
    LLM_API_KEY: Optional[str] = os.getenv("LLM_API_KEY", os.getenv("AI_API_KEY", None))
    EMBEDDING_BASE_URL: Optional[str] = os.getenv("EMBEDDING_BASE_URL", None)
    EMBEDDING_API_KEY: Optional[str] = os.getenv("EMBEDDING_API_KEY", os.getenv("AI_API_KEY", None))

    # Ollama LLM / Fallback Defaults
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", os.getenv("LLM_MODEL", "llama3.2"))
    OLLAMA_TIMEOUT: float = float(os.getenv("OLLAMA_TIMEOUT", "120"))
    OLLAMA_EMBEDDING_MODEL: str = os.getenv("OLLAMA_EMBEDDING_MODEL", os.getenv("EMBEDDING_MODEL", "nomic-embed-text"))
    OLLAMA_EMBEDDING_TIMEOUT: float = float(os.getenv("OLLAMA_EMBEDDING_TIMEOUT", "120"))

    # RAG Configuration
    CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", "500"))
    CHUNK_OVERLAP: int = int(os.getenv("CHUNK_OVERLAP", "100"))
    TOP_K: int = int(os.getenv("TOP_K", "5"))

    class Config:
        case_sensitive = True
        env_file = ".env"
        extra = "ignore"


settings = Settings()
