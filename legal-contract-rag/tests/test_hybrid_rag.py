import pytest
from backend.app.rag.bm25_retriever import tokenize, BM25Retriever
from backend.app.rag.rrf_fusion import RRFFusion
from backend.app.rag.hybrid_retriever import HybridRetriever
from backend.app.core.config import settings


def test_bm25_tokenize():
    text = "Agreement No. VSA-2026-022: Section 1. Delivery terms!"
    tokens = tokenize(text)
    assert "vsa" in tokens or "2026" in tokens
    assert "delivery" in tokens
    assert "section" in tokens


def test_rrf_fusion_mathematics_and_deduplication():
    semantic_results = [
        {"id": "chunk_1", "document": "Clause 1 text", "metadata": {"contract_id": "c1"}, "distance": 0.1},
        {"id": "chunk_2", "document": "Clause 2 text", "metadata": {"contract_id": "c1"}, "distance": 0.3},
    ]
    bm25_results = [
        {"chunk_id": "chunk_2", "text": "Clause 2 text", "contract_id": "c1", "bm25_rank": 1, "bm25_score": 2.5},
        {"chunk_id": "chunk_3", "text": "Clause 3 text", "contract_id": "c1", "bm25_rank": 2, "bm25_score": 1.8},
    ]

    fused = RRFFusion.fuse(semantic_results, bm25_results, rrf_k=60, top_k=5)

    assert len(fused) == 3  # chunk_1, chunk_2, chunk_3 deduplicated
    chunk_ids = [c["chunk_id"] for c in fused]
    assert "chunk_1" in chunk_ids
    assert "chunk_2" in chunk_ids
    assert "chunk_3" in chunk_ids

    # chunk_2 appears in both lists (Semantic rank 2, BM25 rank 1), so its score = (1/(60+2)) + (1/(60+1))
    chunk2_entry = next(c for c in fused if c["chunk_id"] == "chunk_2")
    expected_score = round((1.0 / 62.0) + (1.0 / 61.0), 6)
    assert chunk2_entry["rrf_score"] == expected_score
    assert chunk2_entry["semantic_rank"] == 2
    assert chunk2_entry["bm25_rank"] == 1


def test_contract_scoping_isolation_zero_leakage():
    all_chunks = [
        {"id": "chunk_A1", "contract_id": "contract_A", "text": "Company A termination notice 30 days"},
        {"id": "chunk_B1", "contract_id": "contract_B", "text": "Company B termination notice 60 days"},
    ]

    retriever = BM25Retriever()
    retriever._chunks_cache = all_chunks

    # Query scoped strictly to contract_A
    res_A = retriever.search(query="termination notice", contract_ids=["contract_A"], top_k=5)
    assert len(res_A) == 1
    assert res_A[0]["contract_id"] == "contract_A"
    assert res_A[0]["chunk_id"] == "chunk_A1"

    # Query scoped strictly to contract_B
    res_B = retriever.search(query="termination notice", contract_ids=["contract_B"], top_k=5)
    assert len(res_B) == 1
    assert res_B[0]["contract_id"] == "contract_B"
    assert res_B[0]["chunk_id"] == "chunk_B1"


def is_hit(expected_doc: str, expected_keyword: str, retrieved_chunks: list) -> bool:
    top_3 = retrieved_chunks[:3]
    for chunk in top_3:
        meta = chunk.get("metadata") or {}
        doc_name = meta.get("document_name") or chunk.get("document_name") or ""
        text = chunk.get("document") or chunk.get("text") or ""
        clause = meta.get("clause") or ""

        doc_match = (not expected_doc) or (expected_doc.lower() in doc_name.lower())
        text_match = (not expected_keyword) or (expected_keyword.lower() in text.lower() or expected_keyword.lower() in clause.lower())

        if doc_match and text_match:
            return True
    return False


def test_hit_rate_at_3_calculation():
    retrieved = [
        {"id": "c1", "document_name": "Vendor_Agreement.pdf", "text": "Agreement No. VSA-2026-022 delivery terms"},
        {"id": "c2", "document_name": "Vendor_Agreement.pdf", "text": "Laws of India disputes subject to courts"},
        {"id": "c3", "document_name": "Amendment.pdf", "text": "Article 10 early termination notice"},
    ]

    # Test hit matching expected document and keyword
    hit1 = is_hit(expected_doc="Vendor_Agreement.pdf", expected_keyword="VSA-2026-022", retrieved_chunks=retrieved)
    assert hit1 is True

    # Test miss on non-existent document keyword
    hit2 = is_hit(expected_doc="Vendor_Agreement.pdf", expected_keyword="NonExistentTerm999", retrieved_chunks=retrieved)
    assert hit2 is False
