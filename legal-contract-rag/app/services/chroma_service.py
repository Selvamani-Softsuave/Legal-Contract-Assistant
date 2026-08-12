import chromadb
from chromadb.config import Settings
from app.config import config
import logging
import uuid
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class ChromaService:
    def __init__(self):
        self.client = chromadb.PersistentClient(path=config.CHROMA_PERSIST_DIRECTORY)
        self.collection = self._get_or_create_collection()
    
    def _get_or_create_collection(self):
        """
        Get the existing collection or create a new one.
        """
        try:
            collection = self.client.get_collection(name=config.COLLECTION_NAME)
            logger.info(f"Got existing collection: {config.COLLECTION_NAME}")
            return collection
        except Exception:
            # Collection doesn't exist, create it
            collection = self.client.create_collection(
                name=config.COLLECTION_NAME,
                metadata={"hnsw:space": "cosine"}  # Using cosine similarity
            )
            logger.info(f"Created new collection: {config.COLLECTION_NAME}")
            return collection
    
    def add_document_chunks(
        self, 
        chunks: List[Dict[str, Any]], 
        embeddings: List[List[float]],
        document_id: str,
        document_name: str
    ) -> None:
        """
        Add document chunks to the collection.
        Each chunk should have: text, page, chunk_index.
        """
        try:
            # Prepare data for ChromaDB
            ids = []
            documents = []
            metadatas = []
            
            for i, chunk in enumerate(chunks):
                chunk_id = f"{document_id}_{chunk['page']}_{chunk['chunk_index']}"
                ids.append(chunk_id)
                documents.append(chunk["text"])
                metadatas.append({
                    "document_id": document_id,
                    "document_name": document_name,
                    "page": chunk["page"],
                    "chunk_index": chunk["chunk_index"]
                })
            
            self.collection.add(
                ids=ids,
                documents=documents,
                metadatas=metadatas,
                embeddings=embeddings
            )
            logger.info(f"Added {len(chunks)} chunks for document {document_name}")
        except Exception as e:
            logger.error(f"Error adding chunks to ChromaDB: {e}")
            raise
    
    def similarity_search(
        self, 
        query_embedding: List[float], 
        top_k: int = None
    ) -> List[Dict[str, Any]]:
        """
        Search for similar chunks in the collection.
        Returns a list of dictionaries with keys: id, document, metadata, distance.
        """
        if top_k is None:
            top_k = config.TOP_K
        
        try:
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                include=["documents", "metadatas", "distances"]
            )
            
            # Format results
            formatted_results = []
            if results['ids'] and len(results['ids']) > 0:
                for i in range(len(results['ids'][0])):
                    formatted_results.append({
                        "id": results['ids'][0][i],
                        "document": results['documents'][0][i],
                        "metadata": results['metadatas'][0][i],
                        "distance": results['distances'][0][i]
                    })
            
            return formatted_results
        except Exception as e:
            logger.error(f"Error during similarity search: {e}")
            raise
    
    def get_documents(self) -> List[Dict[str, Any]]:
        """
        Get a list of unique documents in the collection.
        """
        try:
            # Get all metadata to extract unique documents
            results = self.collection.get(include=["metadatas"])
            if not results['metadatas']:
                return []
            
            # Extract unique documents
            docs_map = {}
            for metadata in results['metadatas']:
                doc_id = metadata.get('document_id')
                doc_name = metadata.get('document_name')
                if doc_id and doc_name:
                    if doc_id not in docs_map:
                        docs_map[doc_id] = {
                            "id": doc_id,
                            "name": doc_name,
                            "chunks": 0
                        }
                    docs_map[doc_id]["chunks"] += 1
            
            return list(docs_map.values())
        except Exception as e:
            logger.error(f"Error getting documents: {e}")
            raise
    
    def delete_document(self, document_id: str) -> bool:
        """
        Delete all chunks associated with a document.
        """
        try:
            # Get all chunks for this document
            results = self.collection.get(
                where={"document_id": document_id},
                include=["metadatas"]
            )
            
            if not results['ids']:
                logger.warning(f"No chunks found for document_id: {document_id}")
                return False
            
            # Delete the chunks
            self.collection.delete(ids=results['ids'])
            logger.info(f"Deleted document {document_id} with {len(results['ids'])} chunks")
            return True
        except Exception as e:
            logger.error(f"Error deleting document: {e}")
            raise