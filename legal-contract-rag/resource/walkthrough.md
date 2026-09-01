# Week 5 Final Walkthrough — Evals & Error Analysis (Track F: Legal Contracts)

> **Module**: Week 5 · Module 3 — Evals & Error Analysis (The Core)  
> **Track**: Track F — Legal Contracts  
> **Deliverable**: Open-Coded Trace Analysis, Named Problem Taxonomy, Risk Ranking Matrix (Frequency × Severity), Target Fix Selection, and Excel CSV Dataset Export ([week_5_traces_analysis.csv](file:///e:/Selvamani/Learning/AI%20Learning/legal-contract-rag/week_5_traces_analysis.csv)).

---

## 1. Problem & Objectives

Until Week 4, fixes were applied reactively to whatever errors were noticed. In **Week 5**, we transitioned to systematic evaluation:
1. Captured **20 real execution traces** from live backend endpoints (`/api/v1/chat/conversations/{id}/messages` and `EnterpriseRAGService`).
2. Performed **open-coding**: Wrote a fair, honest single-sentence analysis note for every single trace before deciding on categories.
3. Grouped notes into **named problem types** (Error Taxonomy).
4. Ranked problem types by **Frequency × Severity Risk Score**.
5. Selected the **#1 problem target to fix in Week 6** and wrote an explicit prediction.

---

## 2. Live 20-Trace Execution Results

The 20 traces were executed live against your backend services (with live Ollama embeddings and LLM provider generation):

- **Total Evaluated Traces**: 20
- **`SUCCESS`**: 19 / 20 (**95.0%**)
- **`GENERATION_FAILURE`**: 1 / 20 (**5.0%**)
- **`RETRIEVAL_FAILURE`**: 0 / 20 (**0.0%**)
- **`AMBIGUOUS_INVALID`**: 0 / 20 (**0.0%**)

---

## 3. Named Problem Taxonomy & Frequency × Severity Ranking

$$\text{Risk Score} = \text{Frequency} \times \text{Severity Weight}$$

- **High Severity (3)**: Inaccurate legal terms or false clause summaries.
- **Medium Severity (2)**: Omission of secondary numerical details in legal summaries.
- **Low Severity (1)**: Minor formatting verbosity.

| Rank | Problem Taxonomy Category | Frequency | Severity | Risk Score | Status & Target Selection |
| :---: | :--- | :---: | :---: | :---: | :---: |
| **#1** | **`NUMERICAL_DETAIL_SUMMARY_OMISSION`** | **1 (5%)** | **2 (Medium)** | **2** | 🎯 **SELECTED FIX TARGET FOR WEEK 6** |
| **#2** | **`BOUNDED_CONTEXT_PRECISION`** | 19 (95%) | 0 (None) | 0 | Baseline Passed (95% Accuracy) |

---

## 4. Week 6 Target Fix & Written Prediction

### Target Selected for Fix:
**`NUMERICAL_DETAIL_SUMMARY_OMISSION`** (Rank #1, Risk Score = 2).

### Problem Statement:
When a retrieved legal clause contains multiple numerical constraints (such as `12-month commitment` AND `90-day notice`), the LLM sometimes compresses the clause summary and omits exact day numbers.

### Written Prediction:
1. **System Prompt Directive**: Add an explicit numerical fidelity directive in `LegalRAGPromptBuilder`:
   > *"When summarizing legal clauses containing numerical terms (such as notice days, commitment months, audit limits, or interest percentages), you MUST explicitly state every exact number, percentage, and day limit present in the retrieved text."*
2. **Expected Impact**: `GENERATION_FAILURE` count will drop from **1/20 (5%) to 0/20 (0%)**, increasing overall system accuracy from **95% to 100%**.

---

## 5. Deliverable Files Created

1. **[week_5_traces_analysis.csv](file:///e:/Selvamani/Learning/AI%20Learning/legal-contract-rag/week_5_traces_analysis.csv)**:
   Complete CSV dataset file openable directly in **Microsoft Excel**, containing all 20 trace rows, prompt categories, retrieved source summaries, generated LLM answers, expected reference text, single-sentence open-coded notes, failure classifications, and latency metrics.

2. **[WEEK_5_ERROR_ANALYSIS_TAXONOMY.md](file:///e:/Selvamani/Learning/AI%20Learning/legal-contract-rag/WEEK_5_ERROR_ANALYSIS_TAXONOMY.md)**:
   Formal Markdown specification report with full trace breakdown, open-coding notes, taxonomy rules, risk matrix, and Week 6 target prediction.
