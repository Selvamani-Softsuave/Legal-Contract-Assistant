import os
import logging
from typing import BinaryIO
from backend.app.infrastructure.storage.base import BaseStorageService
from backend.app.core.config import settings

logger = logging.getLogger(__name__)

class AzureBlobStorageService(BaseStorageService):
    def __init__(self):
        self.connection_string = settings.AZURE_STORAGE_CONNECTION_STRING
        self.container_name = settings.BLOB_CONTAINER_NAME
        self.local_fallback_dir = "./documents"
        os.makedirs(self.local_fallback_dir, exist_ok=True)
        self._blob_service_client = None
        self._init_client()

    def _init_client(self):
        try:
            from azure.storage.blob import BlobServiceClient
            if self.connection_string:
                self._blob_service_client = BlobServiceClient.from_connection_string(
                    self.connection_string,
                    api_version="2023-11-03"
                )
                # Ensure container exists
                try:
                    container_client = self._blob_service_client.get_container_client(self.container_name)
                    if not container_client.exists():
                        container_client.create_container()
                except Exception as e:
                    logger.warning(f"Could not initialize container '{self.container_name}': {e}")
        except ImportError:
            logger.warning("azure-storage-blob library not available. Using local disk fallback.")
        except Exception as e:
            logger.warning(f"Failed to connect to Azure Blob Storage / Azurite ({e}). Using local fallback.")

    def upload_file(self, file_obj: BinaryIO, blob_name: str, content_type: str = "application/pdf") -> str:
        if self._blob_service_client:
            try:
                blob_client = self._blob_service_client.get_blob_client(
                    container=self.container_name, blob=blob_name
                )
                file_obj.seek(0)
                blob_client.upload_blob(file_obj, overwrite=True)
                logger.info(f"Uploaded blob '{blob_name}' to Azure container '{self.container_name}'")
                return f"{self.container_name}/{blob_name}"
            except Exception as e:
                logger.error(f"Error uploading to Blob storage: {e}. Falling back to local disk.")

        # Local disk fallback
        local_path = os.path.join(self.local_fallback_dir, blob_name)
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        file_obj.seek(0)
        with open(local_path, "wb") as f:
            f.write(file_obj.read())
        logger.info(f"Saved file to local disk: {local_path}")
        return f"local://{blob_name}"

    def download_file(self, blob_name: str) -> bytes:
        if self._blob_service_client and not blob_name.startswith("local://"):
            try:
                clean_name = blob_name.replace(f"{self.container_name}/", "")
                blob_client = self._blob_service_client.get_blob_client(
                    container=self.container_name, blob=clean_name
                )
                return blob_client.download_blob().readall()
            except Exception as e:
                logger.error(f"Error downloading blob '{blob_name}': {e}")

        # Local disk fallback
        clean_name = blob_name.replace("local://", "")
        local_path = os.path.join(self.local_fallback_dir, clean_name)
        if os.path.exists(local_path):
            with open(local_path, "rb") as f:
                return f.read()
        raise FileNotFoundError(f"File '{blob_name}' not found in Blob storage or local fallback.")

    def delete_file(self, blob_name: str) -> bool:
        if self._blob_service_client and not blob_name.startswith("local://"):
            try:
                clean_name = blob_name.replace(f"{self.container_name}/", "")
                blob_client = self._blob_service_client.get_blob_client(
                    container=self.container_name, blob=clean_name
                )
                blob_client.delete_blob()
                return True
            except Exception as e:
                logger.error(f"Error deleting blob '{blob_name}': {e}")

        clean_name = blob_name.replace("local://", "")
        local_path = os.path.join(self.local_fallback_dir, clean_name)
        if os.path.exists(local_path):
            os.remove(local_path)
            return True
        return False

    def get_file_url(self, blob_name: str) -> str:
        return f"/api/v1/documents/download?blob_name={blob_name}"
