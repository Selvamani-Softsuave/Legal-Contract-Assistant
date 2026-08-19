from typing import List, Dict, Any
from processor.chunkers.base import BaseChunker

class RecursiveChunker(BaseChunker):
    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 100):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk(self, pages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        chunks = []
        global_index = 0

        for page_info in pages:
            page_num = page_info["page"]
            text = page_info["text"]

            start = 0
            while start < len(text):
                end = start + self.chunk_size
                chunk_text = text[start:end]
                if chunk_text.strip():
                    chunks.append({
                        "text": chunk_text.strip(),
                        "page": page_num,
                        "chunk_index": global_index,
                        "article": "",
                        "section": "",
                        "clause": "",
                        "heading": ""
                    })
                    global_index += 1

                start += self.chunk_size - self.chunk_overlap
                if start >= len(text):
                    break

        return chunks
