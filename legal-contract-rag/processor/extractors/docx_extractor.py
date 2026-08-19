import io
import logging
from typing import List, Dict, Any
from processor.extractors.base import BaseExtractor

logger = logging.getLogger(__name__)

class DocxExtractor(BaseExtractor):
    def extract(self, file_bytes: bytes) -> List[Dict[str, Any]]:
        results = []
        try:
            import docx
            doc = docx.Document(io.BytesIO(file_bytes))
            full_text = []
            for p in doc.paragraphs:
                if p.text.strip():
                    full_text.append(p.text.strip())
            
            combined = "\n\n".join(full_text)
            if combined:
                results.append({"page": 1, "text": combined})
        except Exception as e:
            logger.error(f"Error extracting DOCX: {e}")
            raise ValueError(f"Could not extract DOCX text: {str(e)}")

        return results
