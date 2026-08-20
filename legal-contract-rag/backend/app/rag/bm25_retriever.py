import re
import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from rank_bm25 import BM25Okapi

from backend.app.infrastructure.vector.vector_client import VectorClient

logger = logging.getLogger(__name__)


def tokenize(text: str) -> List[str]:
    if not text:
        return []
    # Tokenize: lowercase and extract alphanumeric tokens
    tokens = re.findall(r"\w+", text.lower())
    return tokens


class BM25Retriever:
    """
    Okapi BM25 Keyword Search Retriever over legal document chunks.
    Preserves strict contract-scoped filtering (0% cross-contract leakage).
    """

    def __init__(self, db: Optional[Session] = None):
        self.db = db
        self.vector_client = VectorClient()
        self._chunks_cache: List[Dict[str, Any]] = []
        self._bm25_model: Optional[BM25Okapi] = None

    def _load_chunks(self) -> List[Dict[str, Any]]:
        """
        Loads searchable chunks from DocumentChunks SQL table or via Vector API.
        """
        if self._chunks_cache:
            return self._chunks_cache

        chunks = []
        # Try loading from SQL Server if DB session is available
        if self.db:
            try:
                from backend.app.domain.models.chunk import DocumentChunk
                from backend.app.domain.models.document import Document

                query = self.db.query(DocumentChunk, Document.file_name).join(
                    Document, DocumentChunk.document_id == Document.id
                ).filter(Document.is_deleted == False)

                db_chunks = query.all()
                for chunk_obj, file_name in db_chunks:
                    chunks.append({
                        "id": chunk_obj.id,
                        "document_id": chunk_obj.document_id,
                        "contract_id": chunk_obj.contract_id,
                        "document_name": file_name,
                        "text": chunk_obj.content or "",
                        "page_number": chunk_obj.page_number or 1,
                        "section": chunk_obj.section or chunk_obj.article or "",
                        "clause": chunk_obj.clause or ""
                    })
            except Exception as e:
                logger.warning(f"Failed to query SQL Server for DocumentChunks: {e}")

        # Fallback to querying vector client if SQL query returned empty or DB session unavailable
        if not chunks:
            try:
                # Retrieve all indexed chunks via Processor HTTP Vector Health/search mock query
                # VectorClient dummy search to retrieve all documents if available
                dummy_embed = [0.0] * 768
                search_res = self.vector_client.search_vectors(query_embedding=dummy_embed, top_k=1000)
                for res in search_res:
                    meta = res.get("metadata") or {}
                    chunks.append({
                        "id": res.get("id"),
                        "document_id": meta.get("document_id"),
                        "contract_id": meta.get("contract_id"),
                        "document_name": meta.get("document_name", "Unknown"),
                        "text": res.get("document") or "",
                        "page_number": meta.get("page", 1),
                        "section": meta.get("section") or meta.get("article") or "",
                        "clause": meta.get("clause") or ""
                    })
            except Exception as e:
                logger.error(f"Failed to load chunks for BM25: {e}")

        self._chunks_cache = chunks
        return chunks

    def search(
        self,
        query: str,
        contract_ids: Optional[List[str]] = None,
        top_k: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Executes Okapi BM25 keyword search over legal document chunks.
        Strictly applies contract_ids pre-filtering for 0% cross-contract leakage.
        """
        if not query or not query.strip():
            return []

        all_chunks = self._load_chunks()
        if not all_chunks:
            return []

        # 1. Apply contract-scoped filtering
        if contract_ids:
            target_ids = set(contract_ids)
            filtered_chunks = [c for c in all_chunks if c.get("contract_id") in target_ids]
        else:
            filtered_chunks = all_chunks

        if not filtered_chunks:
            return []

        # 2. Tokenize corpus & query
        corpus_tokens = [tokenize(c["text"]) for c in filtered_chunks]
        query_tokens = tokenize(query)

        if not query_tokens:
            return []

        # 3. Compute BM25 Okapi scores
        bm25 = BM25Okapi(corpus_tokens)
        scores = bm25.get_scores(query_tokens)

        # 4. Rank and format results
        ranked_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)

        results = []
        for rank_idx, idx in enumerate(ranked_indices[:top_k], start=1):
            score = float(scores[idx])
            chunk = filtered_chunks[idx]
            results.append({
                "chunk_id": chunk["id"],
                "document_id": chunk.get("document_id"),
                "contract_id": chunk.get("contract_id"),
                "document_name": chunk.get("document_name", "Unknown"),
                "page_number": chunk.get("page_number", 1),
                "section": chunk.get("section", ""),
                "clause": chunk.get("clause", ""),
                "text": chunk.get("text", ""),
                "bm25_score": round(score, 4),
                "bm25_rank": rank_idx
            })

        return results
