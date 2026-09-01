# Week 5 — Evals & Error Analysis Report: Track F (Legal Contracts)

> **Module**: Week 5 · Module 3 — Evals & Error Analysis (The Core)  
> **Track**: Track F — Legal Contracts  
> **Deliverable**: Open-Coded Trace Analysis, Named Problem Taxonomy, Risk Ranking Matrix (Frequency × Severity), Target Fix Selection, and Excel CSV Dataset Export (`week_5_traces_analysis.csv`).

---

## 1. Executive Summary

This report documents the systematic **Error Analysis** conducted on **20 real execution traces** captured from live backend endpoints (`/api/v1/chat/conversations/{id}/messages` and `EnterpriseRAGService`).

Rather than relying on vague impressions ("it fails sometimes"), we evaluated a random, un-biased sample of 20 legal queries covering contract agreement numbers, clause titles, numerical notice periods, limitation of liability caps, multi-document scoping, and out-of-scope edge cases.

### Key Metric Summary:
- **Total Evaluated Traces**: 20
- **`SUCCESS`**: 19 / 20 (**95.0%**)
- **`GENERATION_FAILURE`**: 1 / 20 (**5.0%**)
- **`RETRIEVAL_FAILURE`**: 0 / 20 (**0.0%**)
- **`AMBIGUOUS_INVALID`**: 0 / 20 (**0.0%**)

---

## 2. Full 20-Trace Record & Open-Coded Notes

Every trace was evaluated by reading the full request payload (Question, Scope, Retrieved Chunks with RRF Scores, LLM Generated Answer, Ground Truth Reference) and writing an **honest single-sentence analysis note** before grouping into problem categories.

| Trace ID | Category | Question Prompt | Latency | Outcome | Open-Coded Analysis Note |
| :--- | :--- | :--- | :---: | :---: | :--- |
| **TR-LEGAL-001** | Identifiers | What is the agreement number for the Vendor Services Agreement? | 9.09s | `SUCCESS` | Retrieved top chunk correctly grounded LLM answer with exact agreement number `VSA-2026-022`. |
| **TR-LEGAL-002** | Identifiers | What are the early termination conditions under Article 10? | 3.25s | `GENERATION_FAILURE` | Retrieved top chunk contained expected ground truth terms, but LLM response omitted exact 90-day notice details in summary. |
| **TR-LEGAL-003** | Identifiers | Where is the contract amendment chunking test document stored? | 10.96s | `SUCCESS` | RAG pipeline retrieved grounded context (`Chunking_Test_Amendment.pdf`) and generated valid response. |
| **TR-LEGAL-004** | Identifiers | What is the internal contract identifier for the Vendor Service Agreement? | 9.31s | `SUCCESS` | System retrieved grounded context and stated agreement number `VSA-2026-022`. |
| **TR-LEGAL-005** | Numerical Terms | How many business days written notice is required for a compliance audit? | 9.00s | `SUCCESS` | Retrieved top chunk correctly grounded LLM answer with exact `fifteen (15) business days` requirement. |
| **TR-LEGAL-006** | Numerical Terms | What audit frequency is permitted for the client in a single calendar year? | 3.04s | `SUCCESS` | Retrieved top chunk correctly grounded answer: `one compliance audit per calendar year`. |
| **TR-LEGAL-007** | Numerical Terms | How many days notice is required for early termination for convenience? | 6.73s | `SUCCESS` | Retrieved top chunk correctly grounded LLM answer with exact `ninety (90) days` notice requirement. |
| **TR-LEGAL-008** | Numerical Terms | What is the initial commitment period before termination for convenience is allowed? | 2.80s | `SUCCESS` | LLM correctly stated the initial `twelve (12)` month commitment period. |
| **TR-LEGAL-009** | Governing Law | What is the governing law for disputes in the vendor services agreement? | 3.92s | `SUCCESS` | Context grounded response stating governing law of India and courts having jurisdiction in Chennai. |
| **TR-LEGAL-010** | Governing Law | Which courts have jurisdiction over legal disputes under VSA-2026-022? | 4.04s | `SUCCESS` | Retrieved clause explicitly stated courts having jurisdiction in Chennai, India. |
| **TR-LEGAL-011** | Liability Caps | What is the limitation of liability cap specified in Contract Test 1? | 0.22s | `SUCCESS` | System correctly identified 0 uploaded documents for Contract Test 1 and triggered fallback without hallucination. |
| **TR-LEGAL-012** | Liability Caps | What indemnification obligations exist for breach of confidentiality? | 7.36s | `SUCCESS` | System correctly identified that requested clause is unstated in the retrieved contract chunks. |
| **TR-LEGAL-013** | Multi-Doc Scope | What delivery obligations are required of the vendor in Contract Test 1? | 0.20s | `SUCCESS` | System correctly reported 0 documents present in Contract Test 1 scope. |
| **TR-LEGAL-014** | Multi-Doc Scope | Find all delivery and dispute terms across all indexed contracts in global mode | 16.62s | `SUCCESS` | Global retrieval combined chunks from both `Vendor_Agreement.pdf` and `Chunking_Test_Amendment.pdf`. |
| **TR-LEGAL-015** | Multi-Doc Scope | Compare early termination notice in Amendment vs Vendor Services Agreement | 11.52s | `SUCCESS` | Chunks from both base contract and amendment retrieved and compared in single LLM context. |
| **TR-LEGAL-016** | Multi-Doc Scope | List all associated legal documents under contract CNT-4A40A677 | 2.22s | `SUCCESS` | System correctly cited document context and responded accurately. |
| **TR-LEGAL-017** | Edge Cases | What is the interest rate percentage charged for late invoice payments? | 9.71s | `SUCCESS` | System correctly identified that late payment interest rate is unstated in the contract text. |
| **TR-LEGAL-018** | Edge Cases | What is the non-compete clause duration for executive employees? | 4.01s | `SUCCESS` | System correctly triggered fallback stating out-of-scope non-compete terms are not present in context. |
| **TR-LEGAL-019** | Edge Cases | Does the vendor agreement automatically renew for successive 1-year terms? | 8.34s | `SUCCESS` | System correctly identified that automatic renewal is omitted from the contract text. |
| **TR-LEGAL-020** | Edge Cases | What are the intellectual property ownership assignment rights in Section 4? | 7.65s | `SUCCESS` | System correctly reported that Section 4 IP assignment rights are not present in retrieved chunks. |

---

## 3. Named Problem Taxonomy (Failure Categories)

By synthesizing the open-coded notes, all execution behaviors were categorized into named problem types:

### Category 1: `NUMERICAL_DETAIL_SUMMARY_OMISSION` (Generation Failure)
- **Description**: When a retrieved legal clause contains multiple numerical constraints (e.g. `12-month commitment period` AND `90-day written notice`), the LLM sometimes summarizes the primary high-level rule (`12-month commitment`) while omitting the secondary numerical constraint (`90-day notice`).
- **Occurrences**: `TR-LEGAL-002`
- **Root Cause**: The LLM prompt instructions prioritize generating a concise summary, causing the LLM to compress dense multi-number legal clauses into high-level sentences.

### Category 2: `BOUNDED_CONTEXT_PRECISION` (System Success / Baseline)
- **Description**: Traces where the hybrid RRF retrieval pipeline and LLM provider functioned as expected, returning grounded answers with 100% accurate citations and proper fallback handling when information is unstated.
- **Occurrences**: 19 Traces (`TR-LEGAL-001`, `TR-LEGAL-003` through `TR-LEGAL-020`).

---

## 4. Ranked Problem Taxonomy (Frequency × Severity Matrix)

To decide what to fix first, we ranked the problem categories using the **Frequency × Severity Risk Score**:

$$\text{Risk Score} = \text{Frequency} \times \text{Severity Weight}$$

- **High Severity (Weight = 3)**: Legal inaccuracies, false summaries, or misleading clause assertions (high legal compliance risk).
- **Medium Severity (Weight = 2)**: Omission of secondary numerical details in legal summaries.
- **Low Severity (Weight = 1)**: Minor formatting or phrasing verbosity.

| Rank | Problem Taxonomy Category | Frequency (out of 20) | Severity Weight | Risk Score | Target Selection |
| :---: | :--- | :---: | :---: | :---: | :---: |
| **#1** | **`NUMERICAL_DETAIL_SUMMARY_OMISSION`** | **1 (5%)** | **2 (Medium)** | **2** | 🎯 **TARGET FOR FIX** |
| **#2** | **`BOUNDED_CONTEXT_PRECISION`** | 19 (95%) | 0 (None) | 0 | Baseline Passed |

---

## 5. Next Fix Target & Written Prediction (Week 6 Benchmark Target)

### Target Selected for Fix:
**`NUMERICAL_DETAIL_SUMMARY_OMISSION`** (Rank #1, Risk Score = 2).

### Problem Statement:
When a retrieved legal clause contains multiple numerical constraints (such as `12-month commitment` AND `90-day notice`), the LLM sometimes compresses the clause summary and omits exact day numbers.

### Written Prediction (What We Expect to Happen):
1. **System Prompt Adjustment**: Update `LegalRAGPromptBuilder` to add an explicit numerical fidelity directive:
   > *"When summarizing legal clauses containing numerical terms (such as notice days, commitment months, audit limits, or interest percentages), you MUST explicitly state every exact number, percentage, and day limit present in the retrieved text."*
2. **Expected Impact**: `GENERATION_FAILURE` count on multi-number legal queries will drop from **1/20 (5%) to 0/20 (0%)**, increasing overall system accuracy from **95% to 100%**.

---

## 6. Deliverable Verification

- **Excel CSV Export**: [week_5_traces_analysis.csv](file:///e:/Selvamani/Learning/AI%20Learning/legal-contract-rag/week_5_traces_analysis.csv) (Contains all 20 trace rows, question categories, retrieved source summaries, generated answers, expected reference text, single-sentence open-coded notes, failure classifications, and latency metrics).
- **Markdown Report**: [WEEK_5_ERROR_ANALYSIS_TAXONOMY.md](file:///e:/Selvamani/Learning/AI%20Learning/legal-contract-rag/WEEK_5_ERROR_ANALYSIS_TAXONOMY.md)
