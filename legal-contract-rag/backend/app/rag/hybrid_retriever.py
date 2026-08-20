import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.infrastructure.vector.vector_client import VectorClient
from backend.app.services.embedding_service import EmbeddingService
from backend.app.rag.bm25_retriever import BM25Retriever
from backend.app.rag.rrf_fusion import RRFFusion

logger = logging.getLogger(__name__)


class HybridRetriever:
    """
    Hybrid Legal Contract Retriever orchestrating Semantic Vector Search,
    Okapi BM25 Keyword Search, and Reciprocal Rank Fusion (RRF).
    Preserves strict contract scoping (0% cross-contract leakage).
    """

    def __init__(self, db: Optional[Session] = None):
        self.db = db
        self.vector_client = VectorClient()
        self.embedding_service = EmbeddingService()
        self.bm25_retriever = BM25Retriever(db=db)

    def search(
        self,
        query: str,
        contract_ids: Optional[List[str]] = None,
        top_k: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Executes hybrid retrieval or semantic-only retrieval based on settings.HYBRID_RETRIEVAL_ENABLED.
        """
        final_k = top_k or settings.HYBRID_FINAL_TOP_K or settings.TOP_K

        # 1. Semantic-Only Fallback (when HYBRID_RETRIEVAL_ENABLED is False)
        query_embedding = self.embedding_service.get_embedding(query)
        semantic_results = self.vector_client.search_vectors(
            query_embedding=query_embedding,
            top_k=settings.SEMANTIC_TOP_K,
            contract_ids=contract_ids
        )

        if not settings.HYBRID_RETRIEVAL_ENABLED:
            logger.info("Hybrid retrieval disabled. Returning semantic-only vector search results.")
            return {
                "results": semantic_results[:final_k],
                "semantic_results": semantic_results,
                "bm25_results": [],
                "fused_results": semantic_results[:final_k]
            }

        # 2. BM25 Keyword Search
        bm25_results = self.bm25_retriever.search(
            query=query,
            contract_ids=contract_ids,
            top_k=settings.BM25_TOP_K
        )

        # 3. Reciprocal Rank Fusion
        fused_results = RRFFusion.fuse(
            semantic_results=semantic_results,
            bm25_results=bm25_results,
            rrf_k=settings.RRF_K,
            top_k=final_k
        )

        logger.info(
            f"Hybrid retrieval finished | Semantic chunks: {len(semantic_results)} | "
            f"BM25 chunks: {len(bm25_results)} | Fused Top-K: {len(fused_results)}"
        )

        return {
            "results": fused_results,
            "semantic_results": semantic_results,
            "bm25_results": bm25_results,
            "fused_results": fused_results
        }
