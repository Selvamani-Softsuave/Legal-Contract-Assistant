#!/usr/bin/env python
"""
Test script to verify the Legal Contract RAG application setup.
Checks that:
1. All application services import successfully
2. Ollama service is running and accessible
3. Local Ollama embedding model (nomic-embed-text) is ready
4. Local Ollama LLM model (llama3.2) is ready
"""

import asyncio
import sys
import os

# Set stdout/stderr encoding to utf-8 for Windows console support
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))


def test_services_import():
    """Test that all services can be imported"""
    try:
        from app.services.embedding_service import EmbeddingService
        from app.services.chroma_service import ChromaService
        from app.services.ollama_service import OllamaService
        from app.services.rag_service import RAGService
        print("[PASS] All services imported successfully")
        return True
    except Exception as e:
        print(f"[FAIL] Failed to import services: {e}")
        return False


async def test_ollama_llm():
    """Test that Ollama LLM is running and accessible"""
    try:
        from app.services.ollama_service import OllamaService
        ollama_service = OllamaService()
        health = await ollama_service.health_check()
        
        print("Ollama LLM Service Check:")
        print(f"  Status: {health.get('status', 'unknown')}")
        print(f"  Ollama connection: {health.get('ollama', 'unknown')}")
        print(f"  LLM Model (llama3.2) available: {health.get('model_available')}")
        
        if health.get('status') == 'healthy' and health.get('model_available') == True:
            print("  [PASS] Ollama LLM is ready!")
            return True
        else:
            print("  [FAIL] Ollama LLM is not ready. Make sure to run: ollama pull llama3.2")
            return False
    except Exception as e:
        print(f"[FAIL] Failed to connect to Ollama LLM: {e}")
        return False


def test_ollama_embeddings():
    """Test that Ollama embedding service (nomic-embed-text) works"""
    try:
        from app.services.embedding_service import EmbeddingService
        embedding_service = EmbeddingService()
        vector = embedding_service.get_embedding("Test embedding connection")
        print("Ollama Embedding Service Check:")
        print(f"  Model ({embedding_service.model}) dimension: {len(vector)}")
        print("  [PASS] Ollama Embedding Service is ready!")
        return True
    except Exception as e:
        print(f"[FAIL] Failed to generate embeddings: {e}")
        print("  Make sure to run: ollama pull nomic-embed-text")
        return False


async def main():
    print("=" * 60)
    print("Legal Contract RAG Application Setup Test (100% Local)")
    print("=" * 60)
    print()
    
    print("1. Testing service imports...")
    imports_ok = test_services_import()
    print()
    
    print("2. Testing Ollama LLM (llama3.2)...")
    ollama_ok = await test_ollama_llm()
    print()
    
    print("3. Testing Ollama Embeddings (nomic-embed-text)...")
    embeddings_ok = test_ollama_embeddings()
    print()
    
    print("=" * 60)
    print("SUMMARY:")
    print(f"  Service imports:     {'PASS' if imports_ok else 'FAIL'}")
    print(f"  Ollama LLM:          {'PASS' if ollama_ok else 'FAIL'}")
    print(f"  Ollama Embeddings:   {'PASS' if embeddings_ok else 'FAIL'}")
    print()
    
    if imports_ok and ollama_ok and embeddings_ok:
        print("[SUCCESS] All checks passed! The local RAG application is fully operational:")
        print("   uvicorn app.main:app --reload")
        return 0
    else:
        print("[FAIL] Some checks failed. Please fix the issues above before running the application.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
