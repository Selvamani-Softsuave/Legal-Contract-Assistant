import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # --- Ollama LLM settings ---
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "llama3.2")
    OLLAMA_TIMEOUT: int = int(os.getenv("OLLAMA_TIMEOUT", 120))

    # --- Ollama Embedding settings ---
    OLLAMA_EMBEDDING_MODEL: str = os.getenv("OLLAMA_EMBEDDING_MODEL", "nomic-embed-text")
    OLLAMA_EMBEDDING_TIMEOUT: int = int(os.getenv("OLLAMA_EMBEDDING_TIMEOUT", 120))
    OLLAMA_EMBEDDING_BATCH_SIZE: int = int(os.getenv("OLLAMA_EMBEDDING_BATCH_SIZE", 10))

    # --- ChromaDB settings ---
    CHROMA_PERSIST_DIRECTORY: str = os.getenv("CHROMA_PERSIST_DIRECTORY", "./chroma_data")
    COLLECTION_NAME: str = os.getenv("COLLECTION_NAME", "legal_contracts")

    # --- RAG settings ---
    CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", 500))
    CHUNK_OVERLAP: int = int(os.getenv("CHUNK_OVERLAP", 100))
    TOP_K: int = int(os.getenv("TOP_K", 5))


config = Config()
