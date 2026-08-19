import io
import pypdf
import logging
from typing import List, Dict, Any
from processor.extractors.base import BaseExtractor

logger = logging.getLogger(__name__)

class PDFExtractor(BaseExtractor):
    def extract(self, file_bytes: bytes) -> List[Dict[str, Any]]:
        results = []
        try:
            reader = pypdf.PdfReader(io.BytesIO(file_bytes))
            for i, page in enumerate(reader.pages, start=1):
                text = page.extract_text() or ""
                if text.strip():
                    results.append({"page": i, "text": text.strip()})
        except Exception as e:
            logger.error(f"Error extracting PDF: {e}")
            raise ValueError(f"Could not extract PDF text: {str(e)}")

        return results
