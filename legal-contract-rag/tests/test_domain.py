import pytest
from backend.app.schemas.contract import ContractCreate, ContractResponse
from backend.app.schemas.document import DocumentUploadResponse
from backend.app.domain.enums import ContractStatus, DocumentStatus

def test_contract_create_schema():
    obj = ContractCreate(
        name="Master Agreement",
        contract_type="MSA",
        governing_law="Delaware"
    )
    assert obj.name == "Master Agreement"
    assert obj.governing_law == "Delaware"

def test_document_upload_response_schema():
    resp = DocumentUploadResponse(
        documentId="doc-123",
        contractId="contract-456",
        fileName="contract.pdf",
        fileSize=1024,
        status="Queued",
        jobId="job-789",
        correlationId="corr-000",
        message="Queued"
    )
    assert resp.documentId == "doc-123"
    assert resp.status == "Queued"

def test_enums():
    assert ContractStatus.ACTIVE == "Active"
    assert DocumentStatus.COMPLETED == "Completed"
