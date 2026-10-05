from abc import ABC, abstractmethod
from typing import List, Optional
from backend.app.domain.entities.conversation_entity import Conversation, Message, RAGSource


class IChatRepository(ABC):
    """Port defining the persistence operations for Conversations and Messages."""

    @abstractmethod
    def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """Retrieve conversation by ID."""
        pass

    @abstractmethod
    def list_conversations(self) -> List[Conversation]:
        """List all conversations ordered by creation date."""
        pass

    @abstractmethod
    def save_conversation(self, conversation: Conversation) -> Conversation:
        """Create or update a conversation."""
        pass

    @abstractmethod
    def delete_conversation(self, conversation_id: str) -> bool:
        """Delete conversation and all its messages."""
        pass

    @abstractmethod
    def add_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        sources: Optional[List[dict]] = None
    ) -> Message:
        """Persist a new message in a conversation."""
        pass

    @abstractmethod
    def get_messages(self, conversation_id: str) -> List[Message]:
        """Get all messages and citations for a conversation."""
        pass
