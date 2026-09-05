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

    def _get_queue_client(self):
        if self._queue_client is not None:
            return self._queue_client

        try:
            from azure.storage.queue import QueueClient, BinaryBase64EncodePolicy
            if self.connection_string:
                client = QueueClient.from_connection_string(
                    self.connection_string,
                    self.queue_name,
                    message_encode_policy=BinaryBase64EncodePolicy(),
                    api_version="2023-11-03"
                )
                try:
                    client.create_queue()
                    logger.info(f"Ensured queue '{self.queue_name}' exists in Azurite / Azure Queue.")
                except Exception:
                    pass  # Queue already exists
                self._queue_client = client
                return self._queue_client
        except Exception as e:
            logger.warning(f"Could not connect to Azure Queue / Azurite: {e}")
            return None

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

        client = self._get_queue_client()
        if client:
            try:
                client.send_message(json_data.encode("utf-8"))
                logger.info(f"Enqueued job to Azure queue '{self.queue_name}': {json_data}")
                return True
            except Exception as e:
                logger.warning(f"Initial send_message failed ({e}). Attempting create_queue() and retry...")
                try:
                    client.create_queue()
                    client.send_message(json_data.encode("utf-8"))
                    logger.info(f"Successfully enqueued job to Azure queue '{self.queue_name}' on retry: {json_data}")
                    return True
                except Exception as retry_err:
                    logger.error(f"Failed to send message to Azure Queue on retry: {retry_err}")
                    raise RuntimeError(f"Failed to enqueue job to Azure Queue: {retry_err}") from retry_err

        raise RuntimeError(
            f"Azure Queue client unavailable (Azurite unreachable). "
            f"Could not enqueue job for document {document_id}."
        )

