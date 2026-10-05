from abc import ABC, abstractmethod
from typing import Optional, List


class IJobRepository(ABC):
    """Port defining persistence operations for Document Processing Jobs."""

    @abstractmethod
    def create_job(
        self,
        job_id: str,
        document_id: str,
        operation: str = "PROCESS",
        correlation_id: Optional[str] = None
    ) -> dict:
        """Create a new asynchronous processing job."""
        pass

    @abstractmethod
    def get_job(self, job_id: str) -> Optional[dict]:
        """Get job record by ID."""
        pass

    @abstractmethod
    def update_job_status(self, job_id: str, status: str, error_message: Optional[str] = None) -> Optional[dict]:
        """Update job progress status."""
        pass
