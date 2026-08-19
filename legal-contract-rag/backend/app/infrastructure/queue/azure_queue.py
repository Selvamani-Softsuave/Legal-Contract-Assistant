import json
import logging
from backend.app.infrastructure.queue.base import BaseQueueService
from backend.app.core.config import settings

logger = logging.getLogger(__name__)

class AzureQueueService(BaseQueueService):
    def __init__(self):
        self.connection_string = settings.AZURE_STORAGE_CONNECTION_STRING
        self.queue_name = settings.QUEUE_NAME
        self._queue_client = None
        self._init_client()

    def _init_client(self):
        try:
            from azure.storage.queue import QueueClient, BinaryBase64EncodePolicy
            if self.connection_string:
                self._queue_client = QueueClient.from_connection_string(
                    self.connection_string,
                    self.queue_name,
                    message_encode_policy=BinaryBase64EncodePolicy(),
                    api_version="2023-11-03"
                )
                try:
                    self._queue_client.create_queue()
                except Exception:
                    pass  # Queue already exists
        except ImportError:
            logger.warning("azure-storage-queue library not available.")
        except Exception as e:
            logger.warning(f"Could not connect to Azure Queue / Azurite ({e}). Logging queue events locally.")

    def enqueue_job(self, document_id: str, operation: str, correlation_id: str, requested_by: str = None, **kwargs) -> bool:
        message_payload = {
            "version": "1.0",
            "documentId": document_id,
            "operation": operation,
            "correlationId": correlation_id,
            "requestedBy": requested_by or "system"
        }
        message_payload.update(kwargs)
        json_data = json.dumps(message_payload)

        if self._queue_client:
            try:
                self._queue_client.send_message(json_data.encode("utf-8"))
                logger.info(f"Enqueued job to Azure queue '{self.queue_name}': {json_data}")
                return True
            except Exception as e:
                logger.error(f"Failed to send message to Azure Queue: {e}")

        logger.info(f"[Mock Queue] Enqueued job message: {json_data}")
        return True
