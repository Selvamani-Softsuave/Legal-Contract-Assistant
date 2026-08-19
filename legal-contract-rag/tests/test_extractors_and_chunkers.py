import pytest
from processor.extractors.txt_extractor import TxtExtractor
from processor.chunkers.legal_aware_chunker import LegalAwareChunker
from processor.chunkers.recursive_chunker import RecursiveChunker

def test_txt_extractor():
    extractor = TxtExtractor()
    sample_text = "ARTICLE I\nDefinitions\n\nSection 1.1 Terms."
    pages = extractor.extract(sample_text.encode("utf-8"))
    assert len(pages) == 1
    assert pages[0]["page"] == 1
    assert "ARTICLE I" in pages[0]["text"]

def test_legal_aware_chunker():
    chunker = LegalAwareChunker(max_chunk_size=500, overlap=50)
    pages = [{
        "page": 1,
        "text": "ARTICLE I\nDEFINITIONS\n\nSection 1.1 Agreement.\nThis Agreement governs the relationship."
    }]
    chunks = chunker.chunk(pages)
    assert len(chunks) > 0
    assert chunks[0]["page"] == 1
    assert "ARTICLE I" in chunks[0]["article"] or "Section 1.1" in chunks[0]["section"]

def test_recursive_chunker_fallback():
    chunker = RecursiveChunker(chunk_size=50, chunk_overlap=10)
    pages = [{"page": 1, "text": "A" * 120}]
    chunks = chunker.chunk(pages)
    assert len(chunks) > 1
    assert chunks[0]["chunk_index"] == 0
