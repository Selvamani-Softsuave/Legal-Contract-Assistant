
import sys
import os
import asyncio
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

from unittest.mock import Mock, patch, AsyncMock

def test_rag_service_answer_question():
    '''Test the RAG service question answering'''
    with patch('services.rag_service.EmbeddingService') as mock_embedding_service, \
         patch('services.rag_service.ChromaService') as mock_chroma_service, \
         patch('services.rag_service.OllamaService') as mock_ollama_service:
        
        # Setup mocks
        mock_embedding_instance = Mock()
        mock_embedding_instance.get_embedding.return_value = [0.1, 0.2, 0.3]
        mock_embedding_service.return_value = mock_embedding_instance
        
        mock_chroma_instance = Mock()
        mock_chroma_instance.similarity_search.return_value = [
            {
                'id': 'chunk1',
                'document': 'This is a test chunk about termination notice.',
                'metadata': {
                    'document_name': 'contract.pdf',
                    'page': 5,
                    'chunk_index': 0
                },
                'distance': 0.1
            }
        ]
        mock_chroma_service.return_value = mock_chroma_instance
        
        # Mock the Ollama service's generate method to be async
        mock_ollama_instance = Mock()
        mock_ollama_instance.generate = AsyncMock(return_value='The termination notice period is 30 days.')
        mock_ollama_service.return_value = mock_ollama_instance
        
        # Import and test
        from services.rag_service import RAGService
        
        rag_service = RAGService()
        # Run the async method
        result = asyncio.run(rag_service.answer_question('What is the termination notice period?'))
        
        # Assertions
        assert 'answer' in result
        assert 'sources' in result
        assert result['answer'] == 'The termination notice period is 30 days.'
        assert len(result['sources']) == 1
        assert result['sources'][0]['document'] == 'contract.pdf'
        assert result['sources'][0]['page'] == 5
        assert result['sources'][0]['chunk'] == 0
        
        # Verify the mocks were called
        mock_embedding_instance.get_embedding.assert_called_once_with('What is the termination notice period?')
        mock_chroma_instance.similarity_search.assert_called_once()
        mock_ollama_instance.generate.assert_called_once()

def test_rag_service_no_results():
    '''Test when no relevant chunks are found'''
    with patch('services.rag_service.EmbeddingService') as mock_embedding_service, \
         patch('services.rag_service.ChromaService') as mock_chroma_service:
        
        mock_embedding_instance = Mock()
        mock_embedding_instance.get_embedding.return_value = [0.1, 0.2, 0.3]
        mock_embedding_service.return_value = mock_embedding_instance
        
        mock_chroma_instance = Mock()
        mock_chroma_instance.similarity_search.return_value = []  # No results
        mock_chroma_service.return_value = mock_chroma_instance
        
        from services.rag_service import RAGService
        
        rag_service = RAGService()
        result = asyncio.run(rag_service.answer_question('What is the company''s tax ID?'))
        
        assert result['answer'] == 'I don''t know based on the provided documents.'
        assert result['sources'] == []

def test_rag_service_ollama_error():
    '''Test when Ollama service returns an error'''
    with patch('services.rag_service.EmbeddingService') as mock_embedding_service, \
         patch('services.rag_service.ChromaService') as mock_chroma_service, \
         patch('services.rag_service.OllamaService') as mock_ollama_service:
        
        mock_embedding_instance = Mock()
        mock_embedding_instance.get_embedding.return_value = [0.1, 0.2, 0.3]
        mock_embedding_service.return_value = mock_embedding_instance
        
        mock_chroma_instance = Mock()
        mock_chroma_instance.similarity_search.return_value = [
            {
                'id': 'chunk1',
                'document': 'This is a test chunk about termination notice.',
                'metadata': {
                    'document_name': 'contract.pdf',
                    'page': 5,
                    'chunk_index': 0
                },
                'distance': 0.1
            }
        ]
        mock_chroma_service.return_value = mock_chroma_instance
        
        # Mock the Ollama service to raise an exception
        mock_ollama_instance = Mock()
        mock_ollama_instance.generate = AsyncMock(side_effect=Exception('Ollama is not available'))
        mock_ollama_service.return_value = mock_ollama_instance
        
        from services.rag_service import RAGService
        
        rag_service = RAGService()
        result = asyncio.run(rag_service.answer_question('What is the termination notice period?'))
        
        assert 'answer' in result
        assert 'Error generating answer:' in result['answer']
        assert result['sources'] == []

if __name__ == '__main__':
    test_rag_service_answer_question()
    test_rag_service_no_results()
    test_rag_service_ollama_error()
    print('RAG tests passed!')

