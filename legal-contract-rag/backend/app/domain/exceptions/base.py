"""
Domain Exceptions - Enterprise Clean Architecture.
Technology-agnostic domain exception hierarchy.
These exceptions represent core business rule violations and domain entity failures.
They MUST NOT contain HTTP or presentation concepts.
"""

class DomainException(Exception):
    """Base class for all enterprise domain exceptions."""
    def __init__(self, message: str, details: dict = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class EntityNotFoundException(DomainException):
    """Raised when an aggregate root or entity cannot be found by its identifier."""
    pass


class EntityAlreadyExistsException(DomainException):
    """Raised when an entity with a unique identifier or business key already exists."""
    pass


class InvalidStateTransitionException(DomainException):
    """Raised when an operation would cause an invalid domain lifecycle transition."""
    pass


class ValidationException(DomainException):
    """Raised when business invariants or domain constraints are violated."""
    pass
