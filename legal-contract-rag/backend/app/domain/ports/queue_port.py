from abc import ABC, abstractmethod
from typing import Dict, Any


class IMessageQueuePort(ABC):
    """Port for asynchronous message dispatching (Azure Queue / RabbitMQ / SQS)."""

    @abstractmethod
    def send_message(self, message: Dict[str, Any]) -> str:
        """Enqueue a message dictionary and return the message ID."""
        pass
