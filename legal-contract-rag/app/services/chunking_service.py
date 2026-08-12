from typing import List, Tuple
from app.config import config

def chunk_text(text_by_page: List[Tuple[int, str]]) -> List[dict]:
    """
    Split text into chunks with overlap.
    Each chunk will have: text, page_number, chunk_index (within the document).
    """
    chunk_size = config.CHUNK_SIZE
    overlap = config.CHUNK_OVERLAP
    
    chunks = []
    for page_num, text in text_by_page:
        # Split the text into chunks for this page
        start = 0
        chunk_index = 0
        while start < len(text):
            end = start + chunk_size
            chunk_text = text[start:end]
            
            chunks.append({
                "text": chunk_text,
                "page": page_num,
                "chunk_index": chunk_index
            })
            
            # Move start for next chunk, accounting for overlap
            start += chunk_size - overlap
            chunk_index += 1
            
            # If we've reached the end of the text, break
            if start >= len(text):
                break
    
    return chunks