from abc import ABC, abstractmethod
from typing import Dict, Any
from backend.app.domain.ports.queue_port import IMessageQueuePort


class BaseQueueService(IMessageQueuePort, ABC):
    """Abstract base queue service extending IMessageQueuePort."""

    @abstractmethod
    def enqueue_job(self, document_id: str, operation: str, correlation_id: str, requested_by: str = None, **kwargs) -> bool:
        """Enqueue a document processing message to the queue."""
        pass

    def send_message(self, message: Dict[str, Any]) -> str:
        """Default IMessageQueuePort implementation delegating to enqueue_job if applicable."""
        doc_id = message.get("document_id", "")
        op = message.get("operation", "PROCESS")
        corr = message.get("correlation_id", "")
        success = self.enqueue_job(document_id=doc_id, operation=op, correlation_id=corr)
        return corr if success else ""
