from abc import ABC, abstractmethod
from backend.app.domain.ports.repositories.contract_repository_port import IContractRepository
from backend.app.domain.ports.repositories.document_repository_port import IDocumentRepository
from backend.app.domain.ports.repositories.chat_repository_port import IChatRepository
from backend.app.domain.ports.repositories.job_repository_port import IJobRepository


class IUnitOfWork(ABC):
    """
    Port defining the atomic transactional boundary across multiple repositories.
    Usage:
        async with uow:
            uow.contracts.save(contract)
            uow.documents.save(document)
            await uow.commit()
    """

    contracts: IContractRepository
    documents: IDocumentRepository
    chat: IChatRepository
    jobs: IJobRepository

    @abstractmethod
    def __enter__(self) -> "IUnitOfWork":
        pass

    @abstractmethod
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    @abstractmethod
    def commit(self) -> None:
        """Commit all pending database changes atomically."""
        pass

    @abstractmethod
    def rollback(self) -> None:
        """Roll back all uncommitted changes."""
        pass
