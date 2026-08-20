from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.repositories.job_repository import JobRepository
from backend.app.schemas.processing import ProcessingJobResponse

router = APIRouter()

@router.get("/jobs/{job_id}", response_model=ProcessingJobResponse)
def get_job_status(job_id: str, db: Session = Depends(get_db)):
    job_repo = JobRepository(db)
    job = job_repo.get_by_id(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Processing job not found")
    return job

from pydantic import BaseModel
from typing import Optional
from backend.app.repositories.document_repository import DocumentRepository
from backend.app.api.v1.ws import manager

class JobStatusUpdate(BaseModel):
    status: str
    error_message: Optional[str] = None
    document_id: str
    page_count: Optional[int] = None
    chunk_count: Optional[int] = None

@router.patch("/jobs/{job_id}/status")
async def update_job_status(job_id: str, obj_in: JobStatusUpdate, db: Session = Depends(get_db)):
    job_repo = JobRepository(db)
    job = job_repo.update_status(job_id, obj_in.status, obj_in.error_message)
    if not job:
        raise HTTPException(status_code=404, detail="Processing job not found")

    if obj_in.document_id:
        doc_repo = DocumentRepository(db)
        doc_repo.update_status(obj_in.document_id, obj_in.status, page_count=obj_in.page_count)

    await manager.broadcast({
        "type": "JOB_UPDATE",
        "document_id": obj_in.document_id,
        "status": obj_in.status,
        "job_id": job_id,
        "page_count": obj_in.page_count
    })

    return {"message": "Status updated successfully"}
