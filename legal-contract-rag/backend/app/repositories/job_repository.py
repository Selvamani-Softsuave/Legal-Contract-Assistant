from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
from backend.app.domain.models.processing_job import ProcessingJob

IN_PROGRESS_STATUSES = {"Processing", "InProgress", "Running"}
TERMINAL_STATUSES = {"Completed", "Failed", "Deleted"}

class JobRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, job_id: str) -> Optional[ProcessingJob]:
        return self.db.query(ProcessingJob).filter(ProcessingJob.id == job_id).first()

    def create(self, job_data: dict) -> ProcessingJob:
        job = ProcessingJob(**job_data)
        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)
        return job

    def update_status(self, job_id: str, status: str, error_message: Optional[str] = None) -> Optional[ProcessingJob]:
        job = self.get_by_id(job_id)
        if not job:
            return None
        job.status = status
        if error_message:
            job.error_message = error_message
        if status in IN_PROGRESS_STATUSES and job.started_at is None:
            job.started_at = datetime.utcnow()
        if status in TERMINAL_STATUSES and job.completed_at is None:
            job.completed_at = datetime.utcnow()
            if job.started_at is None:
                job.started_at = job.completed_at
        self.db.commit()
        self.db.refresh(job)
        return job
