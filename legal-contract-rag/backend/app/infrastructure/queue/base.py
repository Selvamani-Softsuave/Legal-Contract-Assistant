from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseQueueService(ABC):
    @abstractmethod
    def enqueue_job(self, document_id: str, operation: str, correlation_id: str, requested_by: str = None, **kwargs) -> bool:
        """Enqueue a document processing message to the queue."""
        pass
