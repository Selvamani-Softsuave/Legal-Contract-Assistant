import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

from unittest.mock import Mock, patch
import pytest

# We'll test the upload endpoint logic by mocking dependencies
def test_upload_document_mock():
    """Test the document upload process with mocked services"""
    # This is a simplified test - in reality, we'd test the endpoint with TestClient
    # But for simplicity, we'll test the individual service functions
    
    from services.pdf_service import extract_text_from_pdf
    from services.chunking_service import chunk_text
    from services.embedding_service import EmbeddingService
    from services.chroma_service import ChromaService
    
    # Mock the PDF extraction
    with patch('services.pdf_service.extract_text_from_pdf') as mock_extract:
        mock_extract.return_value = [
            (1, "This is a test page."),
            (2, "Another page with more content.")
        ]
        
        # Test the pipeline
        text_by_page = extract_text_from_pdf("dummy.pdf")
        assert len(text_by_page) == 2
        
        chunks = chunk_text(text_by_page)
        assert len(chunks) > 0
        
        # Check chunk structure
        for chunk in chunks:
            assert "text" in chunk
            assert "page" in chunk
            assert "chunk_index" in chunk
            
        # Mock embedding service
        with patch('services.embedding_service.EmbeddingService.get_embeddings') as mock_embed:
            mock_embed.return_value = [[0.1, 0.2, 0.3]] * len(chunks)
            
            embedding_service = EmbeddingService()
            embeddings = embedding_service.get_embeddings([c["text"] for c in chunks])
            assert len(embeddings) == len(chunks)
            
            # Mock chroma service
            with patch('services.chroma_service.ChromaService.add_document_chunks') as mock_add:
                chroma_service = ChromaService()
                chroma_service.add_document_chunks(
                    chunks=chunks,
                    embeddings=embeddings,
                    document_id="test_id",
                    document_name="test.pdf"
                )
                mock_add.assert_called_once()

if __name__ == "__main__":
    test_upload_document_mock()
    print("Ingestion test passed!")