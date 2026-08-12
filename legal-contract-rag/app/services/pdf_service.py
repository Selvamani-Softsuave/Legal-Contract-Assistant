import pypdf
import os
from typing import List, Tuple

def extract_text_from_pdf(file_path: str) -> List[Tuple[int, str]]:
    """
    Extract text from a PDF file, preserving page numbers.
    Returns a list of tuples (page_number, text).
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"PDF file not found: {file_path}")
    
    text_by_page = []
    with open(file_path, 'rb') as file:
        pdf_reader = pypdf.PdfReader(file)
        for page_num, page in enumerate(pdf_reader.pages, start=1):
            text = page.extract_text()
            if text.strip():  # Only add pages with text
                text_by_page.append((page_num, text))
    
    return text_by_page