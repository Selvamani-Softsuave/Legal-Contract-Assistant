from processor.chunkers.base import BaseChunker
from processor.chunkers.recursive_chunker import RecursiveChunker
from processor.chunkers.legal_aware_chunker import LegalAwareChunker

def get_chunker(strategy: str = "legal", chunk_size: int = 800, overlap: int = 100) -> BaseChunker:
    if strategy == "legal":
        return LegalAwareChunker(max_chunk_size=chunk_size, overlap=overlap)
    return RecursiveChunker(chunk_size=chunk_size, chunk_overlap=overlap)

__all__ = [
    "BaseChunker",
    "RecursiveChunker",
    "LegalAwareChunker",
    "get_chunker"
]
