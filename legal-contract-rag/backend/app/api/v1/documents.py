import uuid
import logging
from fastapi import APIRouter, Depends, File, UploadFile, Form, status, Response
from typing import List, Optional
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.repositories.document_repository import DocumentRepository
from backend.app.repositories.job_repository import JobRepository
from backend.app.schemas.document import DocumentUploadResponse, DocumentResponse
from backend.app.application.documents.upload_document_use_case import UploadDocumentUseCase
from backend.app.application.documents.document_use_cases import DocumentUseCases
from backend.app.presentation.dependencies import (
    get_upload_document_use_case,
    get_document_use_cases,
    get_storage_service,
    get_queue_service
)
from backend.app.domain.exceptions.document_exceptions import DocumentNotFoundException

logger = logging.getLogger(__name__)
router = APIRouter()


def _to_document_response(doc) -> DocumentResponse:
    contract_name = doc.contract.name if getattr(doc, "contract", None) else None
    return DocumentResponse(
        id=doc.id,
        contract_id=doc.contract_id,
        contract_name=contract_name,
        file_name=doc.file_name,
        file_size=doc.file_size,
        file_type=doc.file_type,
        blob_path=doc.blob_path,
        page_count=getattr(doc, "page_count", None),
        status=doc.status.value if hasattr(doc.status, "value") else str(doc.status),
        created_at=doc.created_at,
        updated_at=doc.updated_at
    )


@router.post("/upload", response_model=DocumentUploadResponse, status_code=status.HTTP_202_ACCEPTED)
async def upload_document(
    contract_id: str = Form(...),
    file: UploadFile = File(...),
    use_case: UploadDocumentUseCase = Depends(get_upload_document_use_case)
):
    result = use_case.execute(
        contract_id=contract_id,
        filename=file.filename,
        file_obj=file.file,
        file_size=file.size or 0,
        content_type=file.content_type or "application/pdf"
    )

    return DocumentUploadResponse(
        documentId=result["document_id"],
        contractId=contract_id,
        fileName=file.filename,
        fileSize=file.size or 0,
        status=result["status"],
        jobId=result["job_id"],
        correlationId=result["correlation_id"],
        message=result["message"]
    )


@router.get("", response_model=List[DocumentResponse])
def list_all_documents(
    limit: int = 100,
    db: Session = Depends(get_db)
):
    doc_repo = DocumentRepository(db)
    docs = doc_repo.list_all(limit=limit)
    return [_to_document_response(d) for d in docs]


@router.get("/contract/{contract_id}", response_model=List[DocumentResponse])
def list_contract_documents(
    contract_id: str,
    doc_use_cases: DocumentUseCases = Depends(get_document_use_cases)
):
    docs = doc_use_cases.list_documents(contract_id)
    return [_to_document_response(d) for d in docs]


@router.get("/{document_id}", response_model=DocumentResponse)
def get_document(
    document_id: str,
    doc_use_cases: DocumentUseCases = Depends(get_document_use_cases)
):
    doc = doc_use_cases.get_document(document_id)
    return _to_document_response(doc)


@router.get("/{document_id}/download")
def download_document(
    document_id: str,
    doc_use_cases: DocumentUseCases = Depends(get_document_use_cases),
    storage=Depends(get_storage_service)
):
    doc = doc_use_cases.get_document(document_id)
    file_bytes = storage.download_file(doc.blob_path)
    return Response(
        content=file_bytes,
        media_type="application/octet-stream",
        headers={"Content-Disposition": f"attachment; filename={doc.file_name}"}
    )


@router.post("/{document_id}/reprocess", response_model=DocumentUploadResponse, status_code=status.HTTP_202_ACCEPTED)
def reprocess_document(
    document_id: str,
    doc_use_cases: DocumentUseCases = Depends(get_document_use_cases),
    db: Session = Depends(get_db),
    queue=Depends(get_queue_service)
):
    doc = doc_use_cases.get_document(document_id)
    correlation_id = str(uuid.uuid4())
    job_id = str(uuid.uuid4())

    doc_repo = DocumentRepository(db)
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

    try:
        queue.enqueue_job(
            document_id=document_id,
            operation="REPROCESS",
            correlation_id=correlation_id,
            job_id=job_id,
            contract_id=doc.contract_id,
            blob_path=doc.blob_path,
            file_name=doc.file_name
        )
    except Exception as e:
        logger.error(f"Failed to enqueue reprocessing job for document {document_id}: {e}")
        error_msg = "Failed to queue document for reprocessing. Please check that the queue service is running."
        doc_repo.update_status(document_id, "Failed")
        job_repo.update_status(job_id, "Failed", error_msg)
        raise DocumentNotFoundException(document_id)

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
def delete_document(
    document_id: str,
    doc_use_cases: DocumentUseCases = Depends(get_document_use_cases),
    db: Session = Depends(get_db),
    queue=Depends(get_queue_service)
):
    doc = doc_use_cases.get_document(document_id)
    doc_use_cases.delete_document(document_id)

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
    try:
        queue.enqueue_job(
            document_id=document_id,
            operation="DELETE_INDEX",
            correlation_id=correlation_id,
            job_id=job_id
        )
    except Exception as e:
        logger.error(f"Failed to enqueue delete-index job for document {document_id}: {e}")
        job_repo.update_status(job_id, "Failed", "Failed to queue vector purge job.")

    return {"message": "Document deleted and vector purging queued.", "document_id": document_id}
