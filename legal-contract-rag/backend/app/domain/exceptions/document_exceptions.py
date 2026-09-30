from backend.app.domain.exceptions.base import (
    EntityNotFoundException,
    ValidationException,
    InvalidStateTransitionException
)


class DocumentNotFoundException(EntityNotFoundException):
    def __init__(self, document_id: str):
        super().__init__(
            message=f"Document with ID '{document_id}' was not found.",
            details={"document_id": document_id}
        )


class UnsupportedFileTypeException(ValidationException):
    def __init__(self, filename: str, allowed_extensions: tuple):
        super().__init__(
            message=f"File '{filename}' has an unsupported file format. Allowed formats: {', '.join(allowed_extensions)}",
            details={"filename": filename, "allowed_extensions": list(allowed_extensions)}
        )


class FileSizeExceededException(ValidationException):
    def __init__(self, actual_size_bytes: int, max_size_bytes: int):
        super().__init__(
            message=f"File size ({actual_size_bytes / (1024*1024):.2f}MB) exceeds maximum limit of {max_size_bytes / (1024*1024):.0f}MB.",
            details={"actual_size_bytes": actual_size_bytes, "max_size_bytes": max_size_bytes}
        )


class StorageServiceException(ValidationException):
    def __init__(self, operation: str, error_detail: str):
        super().__init__(
            message=f"Storage service operation '{operation}' failed: {error_detail}",
            details={"operation": operation, "error_detail": error_detail}
        )
