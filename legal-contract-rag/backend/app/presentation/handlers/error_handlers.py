import logging
from fastapi import Request, FastAPI, status
from fastapi.responses import JSONResponse
from backend.app.domain.exceptions.base import (
    DomainException,
    EntityNotFoundException,
    EntityAlreadyExistsException,
    InvalidStateTransitionException,
    ValidationException
)
from backend.app.domain.exceptions.document_exceptions import StorageServiceException

logger = logging.getLogger(__name__)


def setup_exception_handlers(app: FastAPI) -> None:
    """Registers global exception translators converting domain errors to RFC 7807 problem details."""

    @app.exception_handler(EntityNotFoundException)
    async def entity_not_found_handler(request: Request, exc: EntityNotFoundException):
        logger.warning(f"Entity not found [{request.url.path}]: {exc.message}")
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "type": "https://errors.enterprise-rag.com/not-found",
                "title": "Resource Not Found",
                "status": status.HTTP_404_NOT_FOUND,
                "detail": exc.message,
                "instance": str(request.url),
                **exc.details
            }
        )

    @app.exception_handler(EntityAlreadyExistsException)
    async def entity_already_exists_handler(request: Request, exc: EntityAlreadyExistsException):
        logger.warning(f"Entity conflict [{request.url.path}]: {exc.message}")
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "type": "https://errors.enterprise-rag.com/conflict",
                "title": "Resource Conflict",
                "status": status.HTTP_400_BAD_REQUEST,
                "detail": exc.message,
                "instance": str(request.url),
                **exc.details
            }
        )

    @app.exception_handler(ValidationException)
    async def validation_exception_handler(request: Request, exc: ValidationException):
        logger.warning(f"Domain validation failed [{request.url.path}]: {exc.message}")
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "type": "https://errors.enterprise-rag.com/validation-error",
                "title": "Validation Failed",
                "status": status.HTTP_400_BAD_REQUEST,
                "detail": exc.message,
                "instance": str(request.url),
                **exc.details
            }
        )

    @app.exception_handler(InvalidStateTransitionException)
    async def state_transition_handler(request: Request, exc: InvalidStateTransitionException):
        logger.warning(f"Invalid state transition [{request.url.path}]: {exc.message}")
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "type": "https://errors.enterprise-rag.com/invalid-state",
                "title": "Invalid Lifecycle Transition",
                "status": status.HTTP_422_UNPROCESSABLE_ENTITY,
                "detail": exc.message,
                "instance": str(request.url),
                **exc.details
            }
        )

    @app.exception_handler(StorageServiceException)
    async def storage_service_error_handler(request: Request, exc: StorageServiceException):
        logger.error(f"Downstream storage service error [{request.url.path}]: {exc.message}")
        return JSONResponse(
            status_code=status.HTTP_502_BAD_GATEWAY,
            content={
                "type": "https://errors.enterprise-rag.com/storage-failure",
                "title": "Storage Service Failure",
                "status": status.HTTP_502_BAD_GATEWAY,
                "detail": exc.message,
                "instance": str(request.url),
                **exc.details
            }
        )
