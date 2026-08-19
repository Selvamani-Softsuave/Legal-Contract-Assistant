import os
from processor.extractors.base import BaseExtractor
from processor.extractors.pdf_extractor import PDFExtractor
from processor.extractors.docx_extractor import DocxExtractor
from processor.extractors.txt_extractor import TxtExtractor

def get_extractor_for_file(filename: str) -> BaseExtractor:
    ext = os.path.splitext(filename.lower())[1]
    if ext == ".pdf":
        return PDFExtractor()
    elif ext in [".docx", ".doc"]:
        return DocxExtractor()
    elif ext in [".txt", ".md"]:
        return TxtExtractor()
    else:
        # Fallback to TxtExtractor
        return TxtExtractor()

__all__ = [
    "BaseExtractor",
    "PDFExtractor",
    "DocxExtractor",
    "TxtExtractor",
    "get_extractor_for_file"
]
