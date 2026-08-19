import httpx
import logging
from typing import List, Dict, Any, Optional
from backend.app.core.config import settings

logger = logging.getLogger(__name__)

class VectorClient:
    def __init__(self):
        self.processor_url = settings.DOCUMENT_PROCESSOR_URL

    def search_vectors(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        contract_ids: Optional[List[str]] = None,
        document_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        url = f"{self.processor_url}/api/vector/search"
        payload = {
            "query_embedding": query_embedding,
            "top_k": top_k,
            "contract_ids": contract_ids,
            "document_id": document_id
        }
        try:
            with httpx.Client(timeout=10.0) as client:
                resp = client.post(url, json=payload)
                resp.raise_for_status()
                data = resp.json()
                return data.get("results", [])
        except Exception as e:
            logger.error(f"Error calling Document Processor vector search API ({url}): {e}")
            return []

    def delete_vectors(self, document_id: str) -> bool:
        url = f"{self.processor_url}/api/vector/delete"
        try:
            with httpx.Client(timeout=10.0) as client:
                resp = client.post(url, json={"document_id": document_id})
                resp.raise_for_status()
                return True
        except Exception as e:
            logger.error(f"Error calling vector delete API ({url}): {e}")
            return False
