from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime
from backend.app.domain.ports.repositories.job_repository_port import IJobRepository
from backend.app.domain.models.processing_job import ProcessingJob


class SQLAlchemyJobRepository(IJobRepository):
    """SQLAlchemy implementation of IJobRepository."""

    def __init__(self, db: Session):
        self.db = db

    def create_job(
        self,
        job_id: str,
        document_id: str,
        operation: str = "PROCESS",
        correlation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        job = ProcessingJob(
            id=job_id,
            document_id=document_id,
            operation=operation,
            correlation_id=correlation_id,
            status="Queued"
        )
        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)
        return {
            "id": job.id,
            "document_id": job.document_id,
            "operation": job.operation,
            "status": job.status,
            "correlation_id": job.correlation_id
        }

    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        job = self.db.query(ProcessingJob).filter(ProcessingJob.id == job_id).first()
        if not job:
            return None
        return {
            "id": job.id,
            "document_id": job.document_id,
            "operation": job.operation,
            "status": job.status,
            "correlation_id": job.correlation_id
        }

    def update_job_status(self, job_id: str, status: str, error_message: Optional[str] = None) -> Optional[Dict[str, Any]]:
        job = self.db.query(ProcessingJob).filter(ProcessingJob.id == job_id).first()
        if not job:
            return None
        job.status = status
        if status == "In_Progress" and not job.started_at:
            job.started_at = datetime.utcnow()
        elif status in ("Completed", "Failed"):
            job.completed_at = datetime.utcnow()
        if error_message:
            job.error_message = error_message
        self.db.commit()
        self.db.refresh(job)
        return {
            "id": job.id,
            "status": job.status,
            "error_message": job.error_message
        }
