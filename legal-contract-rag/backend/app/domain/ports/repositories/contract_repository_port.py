from abc import ABC, abstractmethod
from typing import List, Optional
from backend.app.domain.entities.contract_entity import Contract


class IContractRepository(ABC):
    """Port defining the persistence operations for Contract aggregate roots."""

    @abstractmethod
    def get_by_id(self, contract_id: str) -> Optional[Contract]:
        """Retrieve a contract by its unique ID."""
        pass

    @abstractmethod
    def get_by_number(self, contract_number: str) -> Optional[Contract]:
        """Retrieve a contract by its business contract number."""
        pass

    @abstractmethod
    def list(self, skip: int = 0, limit: int = 100, status: Optional[str] = None) -> List[Contract]:
        """List active non-deleted contracts with optional status filter."""
        pass

    @abstractmethod
    def save(self, contract: Contract) -> Contract:
        """Create or update a contract entity in the persistence store."""
        pass

    @abstractmethod
    def delete(self, contract_id: str) -> bool:
        """Soft delete a contract entity."""
        pass
