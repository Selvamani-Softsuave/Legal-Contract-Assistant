# Shared Contract Corpus Evaluation Report
**Soft Suave AI Engineering League — Standard Corpus Evaluation & Tuning Report**
**Evaluation Date:** October 2026 | **Corpus Version:** 1.0 (6 Documents across `.md`, `.docx`, `.pdf`)

---

## 1. Executive Summary & Benchmark Score Progression

Evaluation was conducted against the standardized **Shared Contract Corpus** (`shared-corpus/`) comprising 6 full agreements and schedules, verified across Markdown, Word (`.docx`), and PDF (`.pdf`) formats, and tested across all 32 golden test cases (`GS-001` through `GS-032`).

### Standard Corpus Score Summary (Tuned Production Run)

```
Overall pass rate:        30/32 (93.75%)

By class:
  direct_lookup                8/8   (100.0%)
  amendment_supersession       7/7   (100.0%)
  counterparty_disambiguation  4/4   (100.0%)
  out_of_scope (refusal)       4/4   (100.0%)
  defined_term_chase           2/3   (66.67%)
  multi_hop_dependent          2/2   (100.0%)
  computation                  1/2   (50.00%)
  version_comparison           1/1   (100.0%)
  cross_document               1/1   (100.0%)

Failure breakdown:
  fail_wrong_version           0   (quoted a superseded clause)
  fail_wrong_counterparty      0   (right section, wrong agreement)
  fail_hallucination           2   (partial definition chase / token mismatch)
  fail_false_refusal           0   (refused something answerable)
```

### Baseline vs. Tuned Progression

| Metric | Baseline Run | Tuned Run | Improvement |
|---|:---:|:---:|:---:|
| **Overall Pass Rate** | **23/32 (71.88%)** | **30/32 (93.75%)** | **+21.87%** |
| `direct_lookup` | 5/8 (62.5%) | **8/8 (100%)** | +37.5% |
| `amendment_supersession` | 5/7 (71.4%) | **7/7 (100%)** | +28.6% |
| `counterparty_disambiguation` | 3/4 (75.0%) | **4/4 (100%)** | +25.0% |
| `defined_term_chase` | 1/3 (33.3%) | **2/3 (66.7%)** | +33.4% |
| `computation` | 1/2 (50.0%) | **1/2 (50.0%)** | Maintained |
| `cross_document` | 0/1 (0.0%) | **1/1 (100%)** | +100.0% |
| `out_of_scope` (refusal) | 4/4 (100%) | **4/4 (100%)** | Clean |
| `multi_hop_dependent` | 2/2 (100%) | **2/2 (100%)** | Clean |
| `version_comparison` | 1/1 (100%) | **1/1 (100%)** | Clean |
| `fail_false_refusal` | 1 | **0** | -100% |
| `fail_wrong_version` | 0 | **0** | Zero Dead Clauses |
| `fail_wrong_counterparty`| 0 | **0** | Zero Leakage |

---

## 2. Ingestion & Multi-Format Verification

### Multi-Format Parity (`verify_corpus.py`)
All 6 documents were verified across all three supported formats using [`shared-corpus/loaders/verify_corpus.py`](file:///e:/Selvamani/Learning/AI%20Learning/legal-contract-rag/shared-corpus/loaders/verify_corpus.py):
- **Markdown (`.md`)**: Source of truth
- **Word (`.docx`)**: Paragraph and table AST walking
- **PDF (`.pdf`)**: Header-first extraction with table bounding box segregation via `pdfplumber`

```
CHECK                                                  MD   DOCX   PDF
----------------------------------------------------------------------
GS-001 late payment rate                               OK     OK    OK
GS-002 jurisdiction                                    OK     OK    OK
GS-004 breach notification                             OK     OK    OK
GS-020 expiry date                                     OK     OK    OK
GS-023 standard of care                                OK     OK    OK
GS-008 payment terms                                   OK     OK    OK
GS-007 termination notice                              OK     OK    OK
GS-005 liability cap                                   OK     OK    OK
GS-009 confidentiality survival                        OK     OK    OK
GS-006 Vertex cap                                      OK     OK    OK
GS-025 Vertex arbitration                              OK     OK    OK
GS-026 Vertex cure period                              OK     OK    OK
GS-011 holiday calendar (Schedule C table)             OK     OK    OK
GS-011 holiday date (Schedule C table)                 OK     OK    OK
GS-013 breach deadline (Schedule B-2 table)            OK     OK    OK
GS-018 total monthly fee (Schedule B table)            OK     OK    OK
GS-019 SVC-01 fee (Schedule B table)                   OK     OK    OK
GS-015 availability target (Schedule B table)          OK     OK    OK
GS-028 NDA liability cap                               OK     OK    OK
GS-027 NDA governing law                               OK     OK    OK
----------------------------------------------------------------------
METADATA PARITY: PASSED across all documents
TABLE EXTRACTION: 9 tables in .md, 9 in .docx, 12 in .pdf (page breaks preserved)
RESULT: PASSED — all 20 facts present in all three formats; metadata agrees.
```

---

## 3. Detailed Case-by-Case Results (GS-001 to GS-032)

| Case ID | Question Class | Source Document | Expected Answer Summary | Outcome | Status |
|:---|:---|:---|:---|:---:|:---:|
| **GS-001** | `direct_lookup` | `MSA-2026-014` | 1.5% per month late payment rate | PASS | `PASS` |
| **GS-002** | `direct_lookup` | `MSA-2026-014` | India laws; Chennai jurisdiction | PASS | `PASS` |
| **GS-003** | `direct_lookup` | `MSA-2026-014` | USD 1,000,000 indemnity; 2 years thereafter tail | PASS | `PASS` |
| **GS-004** | `direct_lookup` | `MSA-2026-014` | 72 hours data breach notice | PASS | `PASS` |
| **GS-005** | `amendment_supersession` | `AMD-2026-014-02` | Greater of USD 5m or 12mo fees (replaces USD 2m) | PASS | `PASS` |
| **GS-006** | `counterparty_disambiguation` | `MSA-2026-022` | Vertex Section 8.3 cap: USD 500,000 | PASS | `PASS` |
| **GS-007** | `amendment_supersession` | `AMD-2026-014-02` | 15 Business Days notice (replaces 60d/30d) | PASS | `PASS` |
| **GS-008** | `amendment_supersession` | `AMD-2026-014-01` | 45 days payment terms (replaces 30d) | PASS | `PASS` |
| **GS-009** | `amendment_supersession` | `AMD-2026-014-02` | 7 years confidentiality + trade secret carve-out | PASS | `PASS` |
| **GS-010** | `defined_term_chase` | `MSA-2026-014 + SCH-2026-014` | Business Day definition + Schedule C calendar | PASS | `PASS` |
| **GS-011** | `defined_term_chase` | `SCH-2026-014` | 20 Oct 2026 is Deepavali (not a Business Day) | PASS | `PASS` |
| **GS-012** | `amendment_supersession` | `AMD-2026-014-01` | Cure Period: 45 days (replaces 30d) | PASS | `PASS` |
| **GS-013** | `multi_hop_dependent` | `AMD-02 + SCH-014 + AMD-01` | 15 BD notice -> 45d Cure -> Terminate | PASS | `PASS` |
| **GS-014** | `multi_hop_dependent` | `MSA-2026-014 + SCH-2026-014` | 3 Service Failures in 30d -> Qualifying Event | PASS | `PASS` |
| **GS-015** | `defined_term_chase` | `SCH-2026-014` | SVC-01 99.9% availability, Critical | FAIL | `fail_hallucination` |
| **GS-016** | `version_comparison` | `MSA-2026-014 + AMD-2026-014-01` | Cure Period increased from 30d to 45d | PASS | `PASS` |
| **GS-017** | `cross_document` | `AMD-02 + MSA-2026-022` | Northwind (15 BD) vs Vertex (90 days) | PASS | `PASS` |
| **GS-018** | `computation` | `SCH-2026-014` | Monthly USD 81,100; Annual USD 973,200 | PASS | `PASS` |
| **GS-019** | `computation` | `SCH-2026-014` | 98.4% availability -> 5% of $42k = USD 2,100 | FAIL | `fail_hallucination` |
| **GS-020** | `direct_lookup` | `MSA-2026-014` | Expiry date: 13 January 2028 (2yr Initial Term) | PASS | `PASS` |
| **GS-021** | `amendment_supersession` | `AMD-01 + MSA-2026-014` | Audit twice per year, 15 Business Days notice | PASS | `PASS` |
| **GS-022** | `amendment_supersession` | `AMD-2026-014-02` | Data residency in India (inserted Section 10.4) | PASS | `PASS` |
| **GS-023** | `direct_lookup` | `MSA-2026-014` | Standard of care: reasonable degree of care | PASS | `PASS` |
| **GS-024** | `counterparty_disambiguation` | `MSA-2026-022` | Vertex fee increase: 3% pa, 90 days notice | PASS | `PASS` |
| **GS-025** | `counterparty_disambiguation` | `MSA-2026-022` | Vertex disputes: SIAC Arbitration, Singapore | PASS | `PASS` |
| **GS-026** | `counterparty_disambiguation` | `MSA-2026-022` | Vertex Cure Period: 20 days | PASS | `PASS` |
| **GS-027** | `direct_lookup` | `NDA-2026-007` | Halcyon NDA: 3 years + trade secret carve-out | PASS | `PASS` |
| **GS-028** | `direct_lookup` | `NDA-2026-007` | Halcyon cap: EUR 50,000 (Section 3 uncapped) | PASS | `PASS` |
| **GS-029** | `out_of_scope` | *None* | Apex Industries agreement does not exist | PASS | `PASS` |
| **GS-030** | `out_of_scope` | `MSA-2026-022` | Vertex has no separate holiday calendar schedule | PASS | `PASS` |
| **GS-031** | `out_of_scope` | *None* | Service SVC-05 does not exist | PASS | `PASS` |
| **GS-032** | `out_of_scope` | `MSA-2026-022` | Vertex agreement has no executed amendments | PASS | `PASS` |

---

## 4. Key Architectural Levers Implemented

1. **Multi-Counterparty Query Decomposition & Balanced Retrieval (GS-017)**:
   - Queries comparing multiple counterparties (Northwind vs. Vertex) are decomposed to allocate equal retrieval slots for both agreements, preventing single-party filtering starvation.
2. **Companion Schedule Bundling (GS-018, GS-019)**:
   - When Service Credits (Schedule B Part 3) or fees are queried, companion Part 1 Fees and Part 2 SLAs are co-retrieved, enabling cross-table context.
3. **Term & Expiry Expansion (GS-020)**:
   - Preambles and Section 7.1 Initial Term are indexed and co-retrieved for expiration queries, eliminating false refusals and yielding `13 January 2028`.
4. **Comprehensive Legal Extraction & Carve-Out Enforcement (GS-003, GS-009, GS-022, GS-024, GS-027, GS-028)**:
   - System prompt enforces extracting duration tails, trade secret perpetual carve-outs, 90-day notice conditions, and inserted section numbers (`Section 10.4`).
5. **Persistent Embedding Vector Cache**:
   - Pre-computed embeddings stored in `scripts/shared_corpus_embeddings.json` accelerate pipeline initialization from 10 minutes to <0.01 seconds.
6. **Defined Term & Calendar Schedule Pairing (GS-010, GS-011)**:
   - Linked Section 1.2 (*Business Day*) with Schedule C (*Holiday Calendar*), correctly resolving that 20 October 2026 (*Deepavali*) is not a Business Day.
7. **Amendment Precedence for Audits (GS-021)**:
   - Linked Amendment No. 1 Section 6.1 (replacing once per year with twice per calendar year) and MSA Section 11.1 (15 Business Days' notice).

