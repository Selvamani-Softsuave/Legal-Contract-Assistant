import pytest
from datetime import datetime, timedelta
from backend.app.domain.entities.contract_entity import Contract
from backend.app.domain.entities.document_entity import Document
from backend.app.domain.entities.conversation_entity import Conversation
from backend.app.domain.enums import ContractStatus, DocumentStatus, MessageRole
from backend.app.domain.value_objects.contract_number import ContractNumber
from backend.app.domain.value_objects.date_range import DateRange
from backend.app.domain.exceptions.contract_exceptions import (
    InvalidContractDateRangeException,
    InvalidContractStatusTransitionException
)
from backend.app.domain.exceptions.base import ValidationException


def test_contract_number_value_object():
    cn = ContractNumber("cnt-12345678")
    assert cn.value == "CNT-12345678"
    assert str(cn) == "CNT-12345678"

    auto_cn = ContractNumber.generate()
    assert auto_cn.value.startswith("CNT-")

    with pytest.raises(ValidationException):
        ContractNumber("")


def test_date_range_validation():
    now = datetime.utcnow()
    valid_range = DateRange(effective_date=now, expiration_date=now + timedelta(days=30))
    assert valid_range.is_active_now is True

    # Expiration earlier than effective date should raise Domain Exception
    with pytest.raises(InvalidContractDateRangeException):
        DateRange(effective_date=now, expiration_date=now - timedelta(days=1))


def test_contract_entity_lifecycle():
    contract = Contract(name="Enterprise Master Agreement")
    assert contract.status == ContractStatus.DRAFT
    assert contract.contract_number.startswith("CNT-")
    assert contract.is_deleted is False

    # Activate
    contract.activate()
    assert contract.status == ContractStatus.ACTIVE

    # Terminate
    contract.terminate()
    assert contract.status == ContractStatus.TERMINATED

    # Re-activating a terminated contract is an invalid domain transition
    with pytest.raises(InvalidContractStatusTransitionException):
        contract.activate()

    # Soft delete
    contract.soft_delete()
    assert contract.is_deleted is True


def test_document_entity_lifecycle():
    doc = Document(
        contract_id="c-1",
        file_name="agreement.pdf",
        file_size=1024,
        file_type="pdf",
        blob_path="c-1/agreement.pdf"
    )
    assert doc.status == DocumentStatus.QUEUED

    doc.mark_processing()
    assert doc.status == DocumentStatus.PROCESSING

    doc.mark_completed()
    assert doc.status == DocumentStatus.COMPLETED

    doc.mark_failed("Extraction timeout")
    assert doc.status == DocumentStatus.FAILED
    assert doc.error_message == "Extraction timeout"


def test_conversation_entity():
    conv = Conversation(title="Legal Review", scoped_contract_ids=["c-1", "c-2"])
    assert conv.title == "Legal Review"
    assert len(conv.messages) == 0

    msg = conv.add_message(MessageRole.USER, "What is the notice period?")
    assert len(conv.messages) == 1
    assert msg.content == "What is the notice period?"
    assert msg.role == MessageRole.USER
