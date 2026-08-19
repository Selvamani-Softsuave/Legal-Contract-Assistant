import logging
from typing import List, Dict, Any
from processor.extractors.base import BaseExtractor

logger = logging.getLogger(__name__)

class TxtExtractor(BaseExtractor):
    def extract(self, file_bytes: bytes) -> List[Dict[str, Any]]:
        try:
            text = file_bytes.decode("utf-8")
        except UnicodeDecodeError:
            text = file_bytes.decode("latin-1", errors="ignore")

        if not text.strip():
            return []

        return [{"page": 1, "text": text.strip()}]
