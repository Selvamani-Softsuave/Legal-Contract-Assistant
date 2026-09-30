from typing import Optional
from sqlalchemy.orm import Session
from backend.app.core.database import SessionLocal
from backend.app.domain.ports.unit_of_work_port import IUnitOfWork
from backend.app.domain.ports.repositories.contract_repository_port import IContractRepository
from backend.app.domain.ports.repositories.document_repository_port import IDocumentRepository
from backend.app.domain.ports.repositories.chat_repository_port import IChatRepository
from backend.app.domain.ports.repositories.job_repository_port import IJobRepository
from backend.app.infrastructure.database.repositories.contract_repository_impl import SQLAlchemyContractRepository
from backend.app.infrastructure.database.repositories.document_repository_impl import SQLAlchemyDocumentRepository
from backend.app.infrastructure.database.repositories.chat_repository_impl import SQLAlchemyChatRepository
from backend.app.infrastructure.database.repositories.job_repository_impl import SQLAlchemyJobRepository


class SQLAlchemyUnitOfWork(IUnitOfWork):
    """
    SQLAlchemy implementation of the Unit of Work pattern.
    Provides atomic transactions across multiple repositories.
    """

    def __init__(self, session_factory=SessionLocal):
        self.session_factory = session_factory
        self.db: Optional[Session] = None

    def __enter__(self) -> "SQLAlchemyUnitOfWork":
        self.db = self.session_factory()
        self.contracts: IContractRepository = SQLAlchemyContractRepository(self.db)
        self.documents: IDocumentRepository = SQLAlchemyDocumentRepository(self.db)
        self.chat: IChatRepository = SQLAlchemyChatRepository(self.db)
        self.jobs: IJobRepository = SQLAlchemyJobRepository(self.db)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.rollback()
        if self.db:
            self.db.close()

    def commit(self) -> None:
        if self.db:
            self.db.commit()

    def rollback(self) -> None:
        if self.db:
            self.db.rollback()
