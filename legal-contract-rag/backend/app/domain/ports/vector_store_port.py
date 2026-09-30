from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional


class IVectorStorePort(ABC):
    """Port defining vector indexing and similarity search operations."""

    @abstractmethod
    def search_vectors(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        contract_ids: Optional[List[str]] = None,
        document_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Perform similarity search and return relevant document chunks."""
        pass

    @abstractmethod
    def delete_vectors(self, document_id: str) -> bool:
        """Delete all vectors associated with a document ID."""
        pass
