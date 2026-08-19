import chromadb
import logging
import os
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class ProcessorChromaService:
    def __init__(self, persist_dir: str = None, collection_name: str = None):
        self.collection_name = collection_name or os.getenv("COLLECTION_NAME", "legal_contracts")
        chroma_host = os.getenv("CHROMA_HOST")
        if chroma_host:
            self.client = chromadb.HttpClient(host=chroma_host, port=int(os.getenv("CHROMA_PORT", "8000")))
        else:
            self.persist_dir = persist_dir or os.getenv("CHROMA_PERSIST_DIRECTORY", "./chroma_data")
            self.client = chromadb.PersistentClient(path=self.persist_dir)
        self.collection = self._get_or_create_collection()

    def _get_or_create_collection(self):
        try:
            collection = self.client.get_collection(name=self.collection_name)
            logger.info(f"Got existing ChromaDB collection: {self.collection_name}")
            return collection
        except Exception:
            collection = self.client.create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}
            )
            logger.info(f"Created new ChromaDB collection: {self.collection_name}")
            return collection

    def add_chunks(
        self,
        document_id: str,
        contract_id: str,
        document_name: str,
        chunks: List[Dict[str, Any]],
        embeddings: List[List[float]]
    ) -> int:
        ids = []
        documents = []
        metadatas = []

        for chunk in chunks:
            chunk_id = f"{document_id}_{chunk.get('page', 1)}_{chunk.get('chunk_index', 0)}"
            ids.append(chunk_id)
            documents.append(chunk["text"])
            metadatas.append({
                "document_id": document_id,
                "contract_id": contract_id,
                "document_name": document_name,
                "page": chunk.get("page", 1),
                "chunk_index": chunk.get("chunk_index", 0),
                "article": chunk.get("article", ""),
                "section": chunk.get("section", ""),
                "clause": chunk.get("clause", ""),
                "heading": chunk.get("heading", "")
            })

        self.collection.add(
            ids=ids,
            documents=documents,
            metadatas=metadatas,
            embeddings=embeddings
        )
        logger.info(f"Indexed {len(chunks)} chunks for document {document_id} in ChromaDB")
        return len(chunks)

    def similarity_search(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        contract_ids: Optional[List[str]] = None,
        document_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        where_filter = {}
        if contract_ids:
            if len(contract_ids) == 1:
                where_filter["contract_id"] = contract_ids[0]
            else:
                where_filter["$or"] = [{"contract_id": cid} for cid in contract_ids]
        elif document_id:
            where_filter["document_id"] = document_id

        kwargs = {
            "query_embeddings": [query_embedding],
            "n_results": top_k,
            "include": ["documents", "metadatas", "distances"]
        }
        if where_filter:
            kwargs["where"] = where_filter

        results = self.collection.query(**kwargs)

        formatted = []
        if results.get("ids") and len(results["ids"]) > 0:
            for i in range(len(results["ids"][0])):
                formatted.append({
                    "id": results["ids"][0][i],
                    "document": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i],
                    "distance": results["distances"][0][i]
                })

        return formatted

    def delete_document_vectors(self, document_id: str) -> bool:
        try:
            results = self.collection.get(where={"document_id": document_id}, include=["metadatas"])
            if results and results.get("ids"):
                self.collection.delete(ids=results["ids"])
                logger.info(f"Deleted {len(results['ids'])} vectors for document {document_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting vectors for document {document_id}: {e}")
            return False

    def clear_vectors() -> bool:
        try:
            self.client.delete_collection(self.collection_name)
            self.collection = self._get_or_create_collection()
            return True
        except Exception as e:
            logger.error(f"Error clearing collection: {e}")
            return False

    def get_health() -> Dict[str, Any]:
        count = self.collection.count()
        return {
            "status": "healthy",
            "collection_name": self.collection_name,
            "total_vectors": count
        }
