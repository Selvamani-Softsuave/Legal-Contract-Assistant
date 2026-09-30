from fastapi import Depends
from sqlalchemy.orm import Session

from backend.app.core.database import get_db, SessionLocal
from backend.app.domain.ports.unit_of_work_port import IUnitOfWork
from backend.app.infrastructure.database.unit_of_work import SQLAlchemyUnitOfWork
from backend.app.infrastructure.database.repositories.contract_repository_impl import SQLAlchemyContractRepository
from backend.app.infrastructure.database.repositories.document_repository_impl import SQLAlchemyDocumentRepository
from backend.app.infrastructure.database.repositories.chat_repository_impl import SQLAlchemyChatRepository
from backend.app.infrastructure.storage.azure_storage import AzureBlobStorageService
from backend.app.infrastructure.queue.azure_queue import AzureQueueService
from backend.app.infrastructure.vector.vector_client import VectorClient

from backend.app.application.contracts.contract_use_cases import ContractUseCases
from backend.app.application.documents.upload_document_use_case import UploadDocumentUseCase
from backend.app.application.documents.document_use_cases import DocumentUseCases
from backend.app.application.chat.chat_use_cases import ChatUseCases


def get_unit_of_work() -> IUnitOfWork:
    return SQLAlchemyUnitOfWork(SessionLocal)


def get_storage_service() -> AzureBlobStorageService:
    return AzureBlobStorageService()


def get_queue_service() -> AzureQueueService:
    return AzureQueueService()


def get_vector_client() -> VectorClient:
    return VectorClient()


def get_contract_use_cases(db: Session = Depends(get_db)) -> ContractUseCases:
    repo = SQLAlchemyContractRepository(db)
    return ContractUseCases(repository=repo)


def get_upload_document_use_case(
    storage=Depends(get_storage_service),
    queue=Depends(get_queue_service),
    uow=Depends(get_unit_of_work)
) -> UploadDocumentUseCase:
    return UploadDocumentUseCase(storage=storage, queue=queue, uow=uow)


def get_document_use_cases(
    db: Session = Depends(get_db),
    storage=Depends(get_storage_service),
    vector_client=Depends(get_vector_client)
) -> DocumentUseCases:
    repo = SQLAlchemyDocumentRepository(db)
    return DocumentUseCases(repository=repo, storage=storage, vector_store=vector_client)


def get_chat_use_cases(db: Session = Depends(get_db)) -> ChatUseCases:
    repo = SQLAlchemyChatRepository(db)
    return ChatUseCases(repository=repo)
