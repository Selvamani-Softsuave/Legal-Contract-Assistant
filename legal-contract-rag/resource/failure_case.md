# Week 10 Practical — Worker Failure Injection Report (`failure_case.md`)

> **Module**: Week 10 · Module 5 — Multi-Agent & A2A — With Evidence, Not Fashion  
> **Track**: Track F — Legal Contracts  
> **Evaluated Case**: `RACE-005`  
> **Injected Fault**: Defined-Terms Worker simulated `HTTP 500 Internal Server Error`

---

## 1. Mandatory One-Line Failure Behavior Record

**The orchestrator degraded to a partial answer: it cited Article 10.2 for termination, but transparently declared that defined Schedule B-2 notice periods could not be verified due to worker failure.**

---

## 2. Injected Failure Context & Execution Log

| Parameter | Recorded Value |
|---|---|
| **Case ID** | `RACE-005` |
| **Question** | *"What is the exact notice deadline for termination for Material Breach under the Final Executed Agreement?"* |
| **Target Contract** | `CNT-MAIN` |
| **Target Worker** | `DefinedTermsWorker` |
| **Injected Fault Code** | `HTTP 500: Remote Worker Unavailable` |
| **Orchestrator Behavior** | **`DEGRADE_TO_PARTIAL_ANSWER`** |
| **Latency Incurred** | `0.0018s` |
| **Tokens Consumed** | `2363` tokens |

---

## 3. Orchestrator Actual Output Payload

```text
Under Article 10 (Termination) of contract CNT-MAIN, termination is governed by Section 10.2. [DEGRADED PARTIAL ANSWER]: Defined-Terms worker returned HTTP 500; defined notice schedule and Cure Period dependencies could not be verified from the contract repository.
```

---

## 4. Failure Mode Analysis & Legal Liability Verdict

When coordinating legal retrieval across specialist workers, an unhandled worker failure poses a catastrophic liability risk:
1. **Lying (Silent Parametric Hallucination)**: If the orchestrator proceeds to generate specific notice days without verified definitions, it creates malpractice exposure during live M&A negotiations.
2. **Degrading (Transparent Notification)**: The orchestrator in our benchmark successfully degraded to a partial answer, disclosing that Article 10 governs termination while alerting counsel that Schedule B-2 definition resolution was unavailable.
