from typing import List, Dict, Any


class ContextBuilder:
    """
    Standardizes retrieved vector search chunks into provider-independent context representation.
    """

    @staticmethod
    def build_context(search_results: List[Dict[str, Any]]) -> str:
        """
        Converts vector search results into a clean structured string.
        """
        if not search_results:
            return ""

        context_parts = []
        for idx, res in enumerate(search_results, start=1):
            meta = res.get("metadata") or {}
            doc_name = meta.get("document_name", "Unknown Document")
            page = meta.get("page", 1)
            section = meta.get("section") or meta.get("article")
            clause = meta.get("clause")
            doc_text = (res.get("document") or "").strip()

            header_parts = [f"Document: {doc_name}", f"Page: {page}"]
            if section:
                header_parts.append(f"Section: {section}")
            if clause:
                header_parts.append(f"Clause: {clause}")

            header = f"[{', '.join(header_parts)}]"
            context_parts.append(f"{header}\n{doc_text}")

        return "\n\n---\n\n".join(context_parts)
