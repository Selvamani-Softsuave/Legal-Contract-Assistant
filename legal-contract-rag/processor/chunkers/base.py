from abc import ABC, abstractmethod
from typing import List, Dict, Any

class BaseChunker(ABC):
    @abstractmethod
    def chunk(self, pages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Chunk list of page objects into structured chunk metadata dictionaries:
        [
           {
             "text": "...",
             "page": 1,
             "chunk_index": 0,
             "article": "ARTICLE I",
             "section": "Section 1.1",
             "clause": "Clause (a)",
             "heading": "Definitions"
           }
        ]
        """
        pass
