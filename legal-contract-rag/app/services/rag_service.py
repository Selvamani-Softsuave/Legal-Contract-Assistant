
from app.services.chroma_service import ChromaService
from app.services.embedding_service import EmbeddingService
from app.services.ollama_service import OllamaService
from app.config import config
import logging
from typing import List

logger = logging.getLogger(__name__)

class RAGService:
    def __init__(self):
        self.chroma_service = ChromaService()
        self.embedding_service = EmbeddingService()
        self.ollama_service = OllamaService()
    
    async def answer_question(self, question: str) -> dict:
        '''
        Answer a question using the RAG pipeline.
        Returns a dictionary with answer and sources.
        '''
        if not question.strip():
            return {
                'answer': 'Please provide a question.',
                'sources': []
            }
        
        # Step 1: Embed the question
        try:
            question_embedding = self.embedding_service.get_embedding(question)
        except Exception as e:
            logger.error(f'Failed to embed question: {e}')
            return {
                'answer': 'Error processing your question.',
                'sources': []
            }
        
        # Step 2: Search for relevant chunks
        try:
            search_results = self.chroma_service.similarity_search(
                query_embedding=question_embedding,
                top_k=config.TOP_K
            )
        except Exception as e:
            logger.error(f'Failed to search ChromaDB: {e}')
            return {
                'answer': 'Error searching documents.',
                'sources': []
            }
        
        # Step 3: Check if we have any results
        if not search_results:
            return {
                'answer': 'I don\'t know based on the provided documents.',
                'sources': []
            }
        
        # Step 4: Build context from search results
        context_parts = []
        sources = []
        for result in search_results:
            context_parts.append(result['document'])
            sources.append({
                'document': result['metadata']['document_name'],
                'page': result['metadata']['page'],
                'chunk': result['metadata']['chunk_index']
            })
        
        context = '\n\n---\n\n'.join(context_parts)
        
        # Step 5: Construct the prompt
        system_prompt = '''You are a legal contract document assistant.

Answer the user's question ONLY using the supplied document context.

Do not use outside knowledge.

Do not invent contract terms.

If the provided context does not contain enough information to answer the question, respond exactly:

'I don\'t know based on the provided documents.'

When answering, cite the document name and page number when available.

The retrieved context is the source of truth.'''
        
        user_prompt = f'''Context:
{context}

Question: {question}

Answer:'''
        
        # Step 6: Call Ollama chat model
        try:
            answer = await self.ollama_service.generate(system_prompt, user_prompt)
        except Exception as e:
            logger.error(f'Error calling Ollama: {e}')
            return {
                'answer': f'Error generating answer: {str(e)}',
                'sources': []
            }
        
        # Step 7: Return answer and sources
        return {
            'answer': answer,
            'sources': sources
        }

