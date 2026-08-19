from sqlalchemy.orm import Session
from typing import Optional
from backend.app.domain.models.processing_job import ProcessingJob

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
        self.db.commit()
        self.db.refresh(job)
        return job
