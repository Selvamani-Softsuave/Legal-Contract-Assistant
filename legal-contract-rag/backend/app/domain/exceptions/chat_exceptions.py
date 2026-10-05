from backend.app.domain.exceptions.base import EntityNotFoundException, ValidationException


class ConversationNotFoundException(EntityNotFoundException):
    def __init__(self, conversation_id: str):
        super().__init__(
            message=f"Conversation with ID '{conversation_id}' was not found.",
            details={"conversation_id": conversation_id}
        )


class EmptyQuestionException(ValidationException):
    def __init__(self):
        super().__init__(
            message="Question cannot be empty or contain only whitespace.",
            details={}
        )
