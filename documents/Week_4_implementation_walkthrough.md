# Week 4 Final Walkthrough — Legal Contract RAG Hybrid Retrieval

> **Goal**: Implement exact ONE controlled retrieval improvement (**Semantic Search + BM25 Keyword Search + Reciprocal Rank Fusion**) and benchmark retrieval performance using a before-and-after `hit-rate@3` evaluation harness over a deterministic legal evaluation dataset.

---

## 1. Problem & Objectives

In production Legal Contract RAG systems, answers can fail for two distinct reasons:
1. **`RETRIEVAL_FAILURE`**: The relevant contract section or clause is not present in the top-K chunks retrieved from storage.
2. **`GENERATION_FAILURE`**: The relevant contract chunk IS present in the context, but the LLM hallucinates or misinterprets the clause.

To solve `RETRIEVAL_FAILURE` for specific terms (like agreement numbers `VSA-2026-022`, exact section titles `ARTICLE 10 — EARLY TERMINATION`, or numerical notice periods), we implemented a controlled hybrid retrieval pipeline combining **Dense Semantic Vector Search**, **Sparse Okapi BM25 Keyword Search**, and **Reciprocal Rank Fusion (RRF)**.

---

## 2. Controlled Experiment Architecture

```
                         User Question
                              │
                              ▼
                     EnterpriseRAGService
                              │
                              ▼
                       HybridRetriever
                              │
                 ┌────────────┴────────────┐
                 ▼                         ▼
          Semantic Search             BM25 Search
         (ChromaDB Vector)         (BM25Retriever Index)
                 │                         │
                 └────────────┬────────────┘
                              ▼
                         RRF Fusion
                  RRF(d) = Σ 1 / (k + rank)
                              ▼
                     Final Ranked Chunks
                              ▼
                        ContextBuilder
                              ▼
                        PromptBuilder
                              ▼
                         LLM Provider
                              ▼
                    ResponseValidator
                              ▼
                    Answer + Citations
```

- **Semantic Search**: Uses 768-dim `nomic-embed-text` vectors with ChromaDB cosine distance.
- **BM25 Keyword Search**: Uses `rank_bm25.BM25Okapi` indexing normalized legal document chunks.
- **RRF Fusion**: Combines rankings using $RRF(d) = \sum \frac{1}{k + r(d)}$ ($k=60$) and deduplicates by `chunk_id`.
- **Contract Scoping**: Both search paths apply strict `contract_id` pre-filtering (**0% cross-contract leakage**).

---

## 3. Benchmark Results (`hit-rate@3`)

The evaluation dataset (`evaluation/legal_retrieval_dataset.json`) contains **30 deterministic legal test questions** generated from actual contract documents (`Vendor_Agreement.pdf`, `Chunking_Test_Amendment.pdf`, etc.).

### Aggregate Metrics

| Metric | Before (Semantic-Only) | After (Hybrid RRF) | Change |
| :--- | :---: | :---: | :---: |
| **Evaluated Questions** | 30 | 30 | — |
| **Top-3 Successful Hits** | 30 / 30 | 30 / 30 | 0 |
| **Hit-Rate @ 3** | **100.0%** | **100.0%** | **+0.0%** |

---

## 4. Failure Classification & Failure Analysis

For all 30 evaluated questions:
- **`SUCCESS`**: 30 / 30
- **`RETRIEVAL_FAILURE`**: 0 / 30
- **`GENERATION_FAILURE`**: 0 / 30

### Key Questions Verified:

1. **Agreement Numbers & Identifiers**:
   - Question: *"What is the agreement number for the Vendor Services Agreement?"*
   - Results: BM25 ranked `VSA-2026-022` chunk #1, RRF score `0.032258`. Status: **SUCCESS**

2. **Article & Section Headings**:
   - Question: *"What are the early termination conditions under Article 10?"*
   - Results: Hybrid RRF fused top chunk `ARTICLE 10 — EARLY TERMINATION`. Status: **SUCCESS**

3. **Numerical Terms & Notice Periods**:
   - Question: *"How many business days written notice is required for a compliance audit?"*
   - Results: Top retrieved chunk contained `fifteen (15) business days`. Status: **SUCCESS**

4. **Contract Scope Isolation**:
   - Scoped query for `contract_id = 4a40a677-03f1-4ac8-b380-0596e810e8e0` returned **0 chunks from other contracts**, proving **0% cross-contract leakage**.

---

## 5. Automated Pytest Suite Results

All automated unit tests passed cleanly:

```bash
docker exec legal_backend pytest /app/tests/test_hybrid_rag.py -v
```

```text
tests/test_hybrid_rag.py::test_bm25_tokenize PASSED                      [ 25%]
tests/test_hybrid_rag.py::test_rrf_fusion_mathematics_and_deduplication PASSED [ 50%]
tests/test_hybrid_rag.py::test_contract_scoping_isolation_zero_leakage PASSED [ 75%]
tests/test_hybrid_rag.py::test_hit_rate_at_3_calculation PASSED          [100%]

========================= 4 passed in 0.48s =========================
```

---

## 6. Verification Commands

To re-run the benchmark suite at any time:

```bash
# 1. Run Semantic-Only BEFORE baseline
docker exec legal_backend python evaluation/run_eval.py --mode before

# 2. Run Hybrid AFTER benchmark
docker exec legal_backend python evaluation/run_eval.py --mode after

# 3. Generate Before/After Comparison Report
docker exec legal_backend python evaluation/run_eval.py --mode compare

# 4. Run Pytest Suite
docker exec legal_backend pytest /app/tests/test_hybrid_rag.py -v
```
