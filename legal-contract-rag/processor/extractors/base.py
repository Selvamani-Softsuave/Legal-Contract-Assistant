from abc import ABC, abstractmethod
from typing import List, Dict, Any, Tuple

class BaseExtractor(ABC):
    @abstractmethod
    def extract(self, file_bytes: bytes) -> List[Dict[str, Any]]:
        """
        Extract text from document bytes.
        Returns a list of page/section dictionaries:
        [
           {"page": 1, "text": "..."},
           {"page": 2, "text": "..."}
        ]
        """
        pass
