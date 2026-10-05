from backend.app.domain.exceptions.base import (
    EntityNotFoundException,
    EntityAlreadyExistsException,
    InvalidStateTransitionException,
    ValidationException
)


class ContractNotFoundException(EntityNotFoundException):
    def __init__(self, contract_id: str):
        super().__init__(
            message=f"Contract with ID '{contract_id}' was not found.",
            details={"contract_id": contract_id}
        )


class DuplicateContractNumberException(EntityAlreadyExistsException):
    def __init__(self, contract_number: str):
        super().__init__(
            message=f"Contract number '{contract_number}' already exists. Please provide a unique contract number.",
            details={"contract_number": contract_number}
        )


class InvalidContractDateRangeException(ValidationException):
    def __init__(self, effective_date, expiration_date):
        super().__init__(
            message=f"Expiration date ({expiration_date}) cannot be earlier than effective date ({effective_date}).",
            details={"effective_date": str(effective_date), "expiration_date": str(expiration_date)}
        )


class InvalidContractStatusTransitionException(InvalidStateTransitionException):
    def __init__(self, current_status: str, target_status: str):
        super().__init__(
            message=f"Cannot transition contract from status '{current_status}' to '{target_status}'.",
            details={"current_status": current_status, "target_status": target_status}
        )
