import re
import logging
from typing import List, Dict, Any
from processor.chunkers.base import BaseChunker
from processor.chunkers.recursive_chunker import RecursiveChunker

logger = logging.getLogger(__name__)

class LegalAwareChunker(BaseChunker):
    def __init__(self, max_chunk_size: int = 800, overlap: int = 100):
        self.max_chunk_size = max_chunk_size
        self.overlap = overlap
        self.fallback = RecursiveChunker(chunk_size=max_chunk_size, chunk_overlap=overlap)

        self.article_pattern = re.compile(r'^(ARTICLE|Article)\s+([IVXLCDM\d]+[:\.]?\s*[^\n]*)', re.MULTILINE)
        self.section_pattern = re.compile(r'^(SECTION|Section)\s+(\d+(\.\d+)?[:\.]?\s*[^\n]*)', re.MULTILINE)
        self.clause_pattern = re.compile(r'^\s*(\([a-z0-9]+\)|[a-z0-9]\.)\s+', re.MULTILINE)

    def chunk(self, pages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        chunks = []
        global_index = 0

        current_article = ""
        current_section = ""
        current_clause = ""
        current_heading = ""

        # First check if document contains legal patterns
        full_text = "\n".join([p["text"] for p in pages])
        has_legal_structure = bool(
            self.article_pattern.search(full_text) or self.section_pattern.search(full_text)
        )

        if not has_legal_structure:
            logger.info("No explicit legal structures found. Using RecursiveChunker fallback.")
            return self.fallback.chunk(pages)

        for page_info in pages:
            page_num = page_info["page"]
            text = page_info["text"]
            paragraphs = text.split("\n\n")

            for para in paragraphs:
                para_str = para.strip()
                if not para_str:
                    continue

                # Check for Article match
                art_match = self.article_pattern.search(para_str)
                if art_match:
                    current_article = art_match.group(0).strip()
                    current_heading = current_article

                # Check for Section match
                sec_match = self.section_pattern.search(para_str)
                if sec_match:
                    current_section = sec_match.group(0).strip()
                    current_heading = current_section

                # Check for Clause match
                cl_match = self.clause_pattern.search(para_str)
                if cl_match:
                    current_clause = cl_match.group(0).strip()

                # Slice large paragraphs if necessary
                if len(para_str) > self.max_chunk_size:
                    sub_start = 0
                    while sub_start < len(para_str):
                        sub_text = para_str[sub_start:sub_start + self.max_chunk_size]
                        chunks.append({
                            "text": sub_text.strip(),
                            "page": page_num,
                            "chunk_index": global_index,
                            "article": current_article,
                            "section": current_section,
                            "clause": current_clause,
                            "heading": current_heading
                        })
                        global_index += 1
                        sub_start += self.max_chunk_size - self.overlap
                else:
                    chunks.append({
                        "text": para_str,
                        "page": page_num,
                        "chunk_index": global_index,
                        "article": current_article,
                        "section": current_section,
                        "clause": current_clause,
                        "heading": current_heading
                    })
                    global_index += 1

        return chunks
