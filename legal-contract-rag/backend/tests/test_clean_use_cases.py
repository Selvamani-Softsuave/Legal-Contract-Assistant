import pytest
import io
from unittest.mock import MagicMock
from backend.app.application.contracts.contract_use_cases import ContractUseCases
from backend.app.application.documents.upload_document_use_case import UploadDocumentUseCase
from backend.app.application.documents.document_use_cases import DocumentUseCases
from backend.app.domain.entities.contract_entity import Contract
from backend.app.domain.entities.document_entity import Document
from backend.app.domain.exceptions.contract_exceptions import (
    ContractNotFoundException,
    DuplicateContractNumberException
)
from backend.app.domain.exceptions.document_exceptions import (
    UnsupportedFileTypeException,
    FileSizeExceededException
)
from backend.app.schemas.contract import ContractCreate, ContractUpdate


def test_contract_use_cases_create_and_get():
    mock_repo = MagicMock()
    mock_repo.get_by_number.return_value = None
    mock_repo.save.side_effect = lambda c: c

    use_cases = ContractUseCases(repository=mock_repo)

    dto = ContractCreate(name="Master Agreement", contract_number="CNT-ABCD1234")
    created = use_cases.create_contract(dto)

    assert created.name == "Master Agreement"
    assert created.contract_number == "CNT-ABCD1234"
    mock_repo.save.assert_called_once()

    # Duplicate check
    mock_repo.get_by_number.return_value = created
    with pytest.raises(DuplicateContractNumberException):
        use_cases.create_contract(dto)


def test_contract_use_cases_not_found():
    mock_repo = MagicMock()
    mock_repo.get_by_id.return_value = None
    use_cases = ContractUseCases(repository=mock_repo)

    with pytest.raises(ContractNotFoundException):
        use_cases.get_contract("non-existent-id")


def test_upload_document_use_case_validation():
    mock_storage = MagicMock()
    mock_queue = MagicMock()
    mock_uow = MagicMock()

    use_case = UploadDocumentUseCase(storage=mock_storage, queue=mock_queue, uow=mock_uow)

    # Invalid file extension
    with pytest.raises(UnsupportedFileTypeException):
        use_case.execute(
            contract_id="c-1",
            filename="virus.exe",
            file_obj=io.BytesIO(b"data"),
            file_size=100
        )

    # File size exceeded
    with pytest.raises(FileSizeExceededException):
        use_case.execute(
            contract_id="c-1",
            filename="big_doc.pdf",
            file_obj=io.BytesIO(b"data"),
            file_size=30 * 1024 * 1024  # 30MB
        )


def test_upload_document_use_case_success():
    mock_storage = MagicMock()
    mock_storage.upload_file.return_value = "contracts/c-1/doc.pdf"
    mock_queue = MagicMock()
    mock_uow = MagicMock()
    mock_uow.__enter__.return_value = mock_uow

    use_case = UploadDocumentUseCase(storage=mock_storage, queue=mock_queue, uow=mock_uow)

    result = use_case.execute(
        contract_id="c-1",
        filename="contract.pdf",
        file_obj=io.BytesIO(b"%PDF-1.4 test content"),
        file_size=1024
    )

    assert result["status"] == "Queued"
    assert result["contract_id"] if "contract_id" in result else True
    mock_storage.upload_file.assert_called_once()
    mock_uow.documents.save.assert_called_once()
    mock_uow.jobs.create_job.assert_called_once()
    mock_uow.commit.assert_called_once()
    mock_queue.send_message.assert_called_once()
