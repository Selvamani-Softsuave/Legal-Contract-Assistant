from abc import ABC, abstractmethod
from typing import BinaryIO, Optional


class IFileStoragePort(ABC):
    """Port for cloud/blob file storage adapters."""

    @abstractmethod
    def upload_file(self, file_obj: BinaryIO, blob_name: str, content_type: str = "application/pdf") -> str:
        """Upload a binary file and return its permanent path/URI."""
        pass

    @abstractmethod
    def download_file(self, blob_name: str) -> bytes:
        """Download binary content of a file."""
        pass

    @abstractmethod
    def delete_file(self, blob_name: str) -> bool:
        """Delete file from storage."""
        pass

    @abstractmethod
    def get_file_url(self, blob_name: str) -> str:
        """Get accessible download URL."""
        pass
