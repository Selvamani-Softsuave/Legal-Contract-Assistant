# Week 10 Practical — 4-Metric Race Table (`race_table.md`)

> **Module**: Week 10 · Module 5 — Multi-Agent & A2A — With Evidence, Not Fashion  
> **Track**: Track F — Legal Contracts  
> **Dataset**: Identical 10 Curated Legal Contract Evaluation Cases (`RACE-001` to `RACE-010`)  
> **Judge**: Same Uniform Factual Assertion Judge

---

## 1. Official 4-Metric Comparison Table (Both Arms)

| Metric | Single Agent (Production Baseline) | Multi-Agent Orchestrator Squad | Delta (Multi vs Single) |
|---|:---:|:---:|:---:|
| **Pass Rate (%)** | **100.0%** (10/10) | **100.0%** (10/10) | **0.0% (TIE)** |
| **p50 Latency (s)** | **0.0001s** | **0.0013s** | **+0.0012s (8.9x slower)** |
| **p99 Latency (s)** | **0.0005s** | **0.0024s** | **+0.0018s (4.6x slower)** |
| **Total Tokens** | **18,091** | **25,019** | **+6,928 tokens** |
| **Cost Per Question ($)** | **$0.000336** | **$0.004503** | **+$0.004167 (13.4x cost)** |

---

## 2. Context Re-send Multiplier Line

**Multi/Single Token Multiplier: 1.4x (Dominant Hand-off: Orchestrator -> Defined-Terms Worker resend, 38.5% of all tokens)**

---

## 3. Per-Case Granular Results (Same 10 Eval Cases)

| Case ID | Question | Single Agent Pass | Multi-Agent Pass | Single Toks | Multi Toks | Multi Latency |
|---|---|:---:|:---:|:---:|:---:|:---:|
| `RACE-001` | What is the notice period required for early terminatio... | ✅ PASS | ✅ PASS | 1048 | 2405 | 0.0014s |
| `RACE-002` | What is the initial commitment period before terminatio... | ✅ PASS | ✅ PASS | 1974 | 2387 | 0.0015s |
| `RACE-003` | What is the governing law for the executed agreement?... | ✅ PASS | ✅ PASS | 1013 | 1362 | 0.0011s |
| `RACE-004` | What is the formal delivery method for notices under Ar... | ✅ PASS | ✅ PASS | 1036 | 1420 | 0.0008s |
| `RACE-005` | What is the exact notice deadline for termination for M... | ✅ PASS | ✅ PASS | 1413 | 3269 | 0.0024s |
| `RACE-006` | If Acme Corp experiences a Change of Control, what is t... | ✅ PASS | ✅ PASS | 1088 | 2397 | 0.0012s |
| `RACE-007` | Under Amendment No. 1, what was the early termination n... | ✅ PASS | ✅ PASS | 1824 | 2238 | 0.0011s |
| `RACE-008` | What are the combined requirements (cure period and sub... | ✅ PASS | ✅ PASS | 1413 | 4114 | 0.0017s |
| `RACE-009` | How did the defined Cure Period change between the Orig... | ✅ PASS | ✅ PASS | 1507 | 3030 | 0.0014s |
| `RACE-010` | Resolve the notice schedule for Circular Term Alpha to ... | ✅ PASS | ✅ PASS | 5775 | 2397 | 0.0013s |
