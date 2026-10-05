from backend.app.domain.ports.repositories.contract_repository_port import IContractRepository
from backend.app.domain.ports.repositories.document_repository_port import IDocumentRepository
from backend.app.domain.ports.repositories.chat_repository_port import IChatRepository
from backend.app.domain.ports.repositories.job_repository_port import IJobRepository

__all__ = [
    "IContractRepository",
    "IDocumentRepository",
    "IChatRepository",
    "IJobRepository",
]
