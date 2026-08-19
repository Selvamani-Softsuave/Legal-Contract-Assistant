from abc import ABC, abstractmethod
from typing import BinaryIO, Optional

class BaseStorageService(ABC):
    @abstractmethod
    def upload_file(self, file_obj: BinaryIO, blob_name: str, content_type: str = "application/pdf") -> str:
        """Upload file object to storage and return blob_path."""
        pass

    @abstractmethod
    def download_file(self, blob_name: str) -> bytes:
        """Download file content by blob_name."""
        pass

    @abstractmethod
    def delete_file(self, blob_name: str) -> bool:
        """Delete file from storage."""
        pass

    @abstractmethod
    def get_file_url(self, blob_name: str) -> str:
        """Get secure download URL or path for a blob."""
        pass
