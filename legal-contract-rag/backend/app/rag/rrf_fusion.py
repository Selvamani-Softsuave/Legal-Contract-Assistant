import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


class RRFFusion:
    """
    Reciprocal Rank Fusion (RRF) for combining Semantic Vector Search
    and BM25 Keyword Search results into a unified, deterministic ranking.
    Formula: RRF_Score(d) = Σ 1 / (k + rank_m(d))
    """

    @staticmethod
    def fuse(
        semantic_results: List[Dict[str, Any]],
        bm25_results: List[Dict[str, Any]],
        rrf_k: int = 60,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Fuses semantic vector search results and BM25 keyword search results.
        Deduplicates chunks by chunk_id and computes combined RRF scores.
        """
        scores: Dict[str, float] = {}
        semantic_ranks: Dict[str, int] = {}
        bm25_ranks: Dict[str, int] = {}
        chunk_map: Dict[str, Dict[str, Any]] = {}

        # 1. Process Semantic Search Ranks
        for rank_idx, res in enumerate(semantic_results, start=1):
            chunk_id = res.get("id") or res.get("chunk_id")
            if not chunk_id:
                continue

            semantic_ranks[chunk_id] = rank_idx
            scores[chunk_id] = scores.get(chunk_id, 0.0) + (1.0 / (rrf_k + rank_idx))

            if chunk_id not in chunk_map:
                meta = res.get("metadata") or {}
                chunk_map[chunk_id] = {
                    "chunk_id": chunk_id,
                    "document_id": meta.get("document_id") or res.get("document_id"),
                    "contract_id": meta.get("contract_id") or res.get("contract_id"),
                    "document_name": meta.get("document_name") or res.get("document_name", "Unknown"),
                    "page_number": meta.get("page") or res.get("page_number", 1),
                    "section": meta.get("section") or meta.get("article") or res.get("section", ""),
                    "clause": meta.get("clause") or res.get("clause", ""),
                    "text": res.get("document") or res.get("text") or "",
                    "distance": res.get("distance")
                }

        # 2. Process BM25 Search Ranks
        for rank_idx, res in enumerate(bm25_results, start=1):
            chunk_id = res.get("chunk_id") or res.get("id")
            if not chunk_id:
                continue

            bm25_ranks[chunk_id] = rank_idx
            scores[chunk_id] = scores.get(chunk_id, 0.0) + (1.0 / (rrf_k + rank_idx))

            if chunk_id not in chunk_map:
                chunk_map[chunk_id] = {
                    "chunk_id": chunk_id,
                    "document_id": res.get("document_id"),
                    "contract_id": res.get("contract_id"),
                    "document_name": res.get("document_name", "Unknown"),
                    "page_number": res.get("page_number", 1),
                    "section": res.get("section", ""),
                    "clause": res.get("clause", ""),
                    "text": res.get("text", "")
                }

        # 3. Sort chunks by RRF score descending with deterministic tie-breaking on chunk_id
        sorted_chunk_ids = sorted(
            scores.keys(),
            key=lambda cid: (scores[cid], cid),
            reverse=True
        )

        # 4. Build unified ranked output list
        fused_results = []
        for final_rank, chunk_id in enumerate(sorted_chunk_ids[:top_k], start=1):
            chunk = chunk_map[chunk_id]
            fused_results.append({
                "id": chunk_id,
                "chunk_id": chunk_id,
                "document_id": chunk.get("document_id"),
                "contract_id": chunk.get("contract_id"),
                "document": chunk.get("text", ""),
                "text": chunk.get("text", ""),
                "metadata": {
                    "document_name": chunk.get("document_name", "Unknown"),
                    "document_id": chunk.get("document_id"),
                    "contract_id": chunk.get("contract_id"),
                    "page": chunk.get("page_number", 1),
                    "section": chunk.get("section", ""),
                    "clause": chunk.get("clause", "")
                },
                "distance": chunk.get("distance", 0.0),
                "semantic_rank": semantic_ranks.get(chunk_id),
                "bm25_rank": bm25_ranks.get(chunk_id),
                "rrf_score": round(scores[chunk_id], 6),
                "final_rank": final_rank
            })

        return fused_results
