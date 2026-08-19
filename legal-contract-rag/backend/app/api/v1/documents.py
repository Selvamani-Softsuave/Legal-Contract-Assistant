import uuid
import logging
from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, Form, status, Response
from fastapi.responses import Response
from sqlalchemy.orm import Session
from typing import List, Optional

from backend.app.core.database import get_db
from backend.app.repositories.document_repository import DocumentRepository
from backend.app.repositories.job_repository import JobRepository
from backend.app.infrastructure.storage.azure_storage import AzureBlobStorageService
from backend.app.infrastructure.queue.azure_queue import AzureQueueService
from backend.app.schemas.document import DocumentUploadResponse, DocumentResponse

logger = logging.getLogger(__name__)
router = APIRouter()

storage_service = AzureBlobStorageService()
queue_service = AzureQueueService()

@router.post("/upload", response_model=DocumentUploadResponse, status_code=status.HTTP_202_ACCEPTED)
async def upload_document(
    contract_id: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    # Validate extension
    allowed_exts = (".pdf", ".docx", ".doc", ".txt")
    if not file.filename.lower().endswith(allowed_exts):
        raise HTTPException(status_code=400, detail="Allowed file formats: PDF, DOCX, TXT")

    document_id = str(uuid.uuid4())
    correlation_id = str(uuid.uuid4())
    job_id = str(uuid.uuid4())
    blob_name = f"{contract_id}/{document_id}_{file.filename}"

    # 1. Upload to Blob storage
    try:
        blob_path = storage_service.upload_file(file.file, blob_name, content_type=file.content_type)
    except Exception as e:
        logger.error(f"Failed to upload file to Blob storage: {e}")
        raise HTTPException(status_code=500, detail="Failed to save document file")
    finally:
        file.file.close()

    # 2. Persist Document relational record
    doc_repo = DocumentRepository(db)
    doc = doc_repo.create({
        "id": document_id,
        "contract_id": contract_id,
        "file_name": file.filename,
        "file_size": file.size or 0,
        "file_type": file.filename.split(".")[-1].lower(),
        "blob_path": blob_path,
        "status": "Queued"
    })

    # 3. Persist ProcessingJob relational record
    job_repo = JobRepository(db)
    job = job_repo.create({
        "id": job_id,
        "document_id": document_id,
        "operation": "PROCESS",
        "status": "Queued",
        "correlation_id": correlation_id,
        "requested_by": "system"
    })

    # 4. Enqueue processing message to legal-document-processing queue
    queue_service.enqueue_job(
        document_id=document_id,
        operation="PROCESS",
        correlation_id=correlation_id,
        job_id=job_id,
        contract_id=contract_id,
        blob_path=blob_path,
        file_name=file.filename
    )

    return DocumentUploadResponse(
        documentId=document_id,
        contractId=contract_id,
        fileName=file.filename,
        fileSize=file.size or 0,
        status="Queued",
        jobId=job_id,
        correlationId=correlation_id,
        message="Document uploaded successfully. Processing job queued."
    )

@router.get("/contract/{contract_id}", response_model=List[DocumentResponse])
def list_contract_documents(contract_id: str, db: Session = Depends(get_db)):
    doc_repo = DocumentRepository(db)
    return doc_repo.list_by_contract(contract_id)

@router.get("/{document_id}", response_model=DocumentResponse)
def get_document(document_id: str, db: Session = Depends(get_db)):
    doc_repo = DocumentRepository(db)
    doc = doc_repo.get_by_id(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc

@router.get("/{document_id}/download")
def download_document(document_id: str, db: Session = Depends(get_db)):
    doc_repo = DocumentRepository(db)
    doc = doc_repo.get_by_id(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    file_bytes = storage_service.download_file(doc.blob_path)
    return Response(
        content=file_bytes,
        media_type="application/octet-stream",
        headers={"Content-Disposition": f"attachment; filename={doc.file_name}"}
    )

@router.post("/{document_id}/reprocess", response_model=DocumentUploadResponse, status_code=status.HTTP_202_ACCEPTED)
def reprocess_document(document_id: str, db: Session = Depends(get_db)):
    doc_repo = DocumentRepository(db)
    doc = doc_repo.get_by_id(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    correlation_id = str(uuid.uuid4())
    job_id = str(uuid.uuid4())

    doc_repo.update_status(document_id, "Queued")
    job_repo = JobRepository(db)
    job_repo.create({
        "id": job_id,
        "document_id": document_id,
        "operation": "REPROCESS",
        "status": "Queued",
        "correlation_id": correlation_id,
        "requested_by": "system"
    })

    queue_service.enqueue_job(
        document_id=document_id, 
        operation="REPROCESS", 
        correlation_id=correlation_id,
        job_id=job_id,
        contract_id=doc.contract_id,
        blob_path=doc.blob_path,
        file_name=doc.file_name
    )

    return DocumentUploadResponse(
        documentId=document_id,
        contractId=doc.contract_id,
        fileName=doc.file_name,
        fileSize=doc.file_size,
        status="Queued",
        jobId=job_id,
        correlationId=correlation_id,
        message="Reprocessing job queued."
    )

@router.delete("/{document_id}", status_code=status.HTTP_202_ACCEPTED)
def delete_document(document_id: str, db: Session = Depends(get_db)):
    doc_repo = DocumentRepository(db)
    doc = doc_repo.get_by_id(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    doc_repo.soft_delete(document_id)
    storage_service.delete_file(doc.blob_path)

    correlation_id = str(uuid.uuid4())
    job_id = str(uuid.uuid4())
    job_repo = JobRepository(db)
    job_repo.create({
        "id": job_id,
        "document_id": document_id,
        "operation": "DELETE_INDEX",
        "status": "Queued",
        "correlation_id": correlation_id
    })
    queue_service.enqueue_job(
        document_id=document_id, 
        operation="DELETE_INDEX", 
        correlation_id=correlation_id,
        job_id=job_id
    )

    return {"message": "Document deleted and vector purging queued.", "document_id": document_id}
