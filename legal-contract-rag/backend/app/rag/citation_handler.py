from typing import List, Dict, Any


class CitationHandler:
    """
    Builds citation DTOs directly from retrieved vector search metadata,
    ensuring the application is the sole source of truth for citations.
    """

    @staticmethod
    def build_sources(search_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        sources = []
        for res in search_results:
            meta = res.get("metadata") or {}
            rrf_score = res.get("rrf_score")
            distance = res.get("distance", 0.0)
            score = rrf_score if rrf_score is not None else float(distance)
            
            sources.append({
                "chunk_id": res.get("id") or res.get("chunk_id"),
                "document_name": meta.get("document_name", "Unknown"),
                "page_number": meta.get("page"),
                "section": meta.get("section") or meta.get("article"),
                "clause": meta.get("clause"),
                "relevance_score": float(score)
            })
        return sources
