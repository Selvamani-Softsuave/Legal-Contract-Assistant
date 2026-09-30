from abc import ABC, abstractmethod
from typing import List, Optional
from backend.app.domain.entities.document_entity import Document


class IDocumentRepository(ABC):
    """Port defining the persistence operations for Document entities."""

    @abstractmethod
    def get_by_id(self, document_id: str) -> Optional[Document]:
        """Retrieve a document by ID."""
        pass

    @abstractmethod
    def list_by_contract(self, contract_id: str) -> List[Document]:
        """List all documents for a specific contract."""
        pass

    @abstractmethod
    def save(self, document: Document) -> Document:
        """Create or update a document."""
        pass

    @abstractmethod
    def update_status(self, document_id: str, status: str, error_message: Optional[str] = None) -> Optional[Document]:
        """Update processing status of a document."""
        pass

    @abstractmethod
    def delete(self, document_id: str) -> bool:
        """Delete a document record."""
        pass
