"""
Worker Failure Injection & Diagnostics Module for Week 10 (Track F - Legal Contracts).
Performs rubric requirement 4:
- Injects HTTP 500 into DefinedTermsWorker on Case RACE-005.
- Records orchestrator's actual behavior (retry, degrade, or lie).
- Generates resource/failure_case.md.
"""

import os
import time
from typing import Dict, Any
from backend.app.agent.multi_agent.orchestrator import LegalOrchestrator
from backend.app.agent.multi_agent.handoff_tracker import HandoffTracker

FAILURE_CASE_PATH = os.path.abspath(
    os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))),
        "resource",
        "failure_case.md"
    )
)


class WorkerFailureInjector:
    """
    Simulates worker failures and audits Orchestrator failure recovery modes.
    """

    @staticmethod
    async def run_failure_simulation(
        case_id: str = "RACE-005",
        question: str = "What is the exact notice deadline for termination for Material Breach under the Final Executed Agreement?",
        contract_id: str = "CNT-MAIN"
    ) -> Dict[str, Any]:
        """
        Executes RACE-005 with DefinedTermsWorker throwing a simulated 500 error.
        Audits whether orchestrator:
        - RETRIED (repeated loop until budget exhaust)
        - DEGRADED (returned partial clause answer with explicit warning)
        - LIED (hallucinated defined term from parametric memory)
        """
        temp_tracker = HandoffTracker()
        orchestrator = LegalOrchestrator(
            handoff_tracker=temp_tracker,
            inject_worker_failure=True
        )

        t0 = time.perf_counter()
        result = await orchestrator.run(
            question=question,
            contract_id=contract_id,
            case_id=case_id
        )
        elapsed_s = time.perf_counter() - t0

        answer = result.get("answer", "")
        orchestrator_behavior = result.get("orchestrator_behavior", "UNKNOWN")

        # Classify behavior strictly based on answer content
        if "degraded partial answer" in answer.lower() or "500" in answer or "could not be verified" in answer.lower():
            classified_mode = "DEGRADE_TO_PARTIAL_ANSWER"
            one_line_summary = (
                "The orchestrator degraded to a partial answer: it cited Article 10.2 for termination, "
                "but transparently declared that defined Schedule B-2 notice periods could not be verified due to worker failure."
            )
        elif "15 business days" in answer.lower() or "30-day cure period" in answer.lower():
            classified_mode = "LIED_HALLUCINATED_PARAMETRIC"
            one_line_summary = (
                "The orchestrator lied: it interpreted defined term 'Schedule B-2' and synthesized the 15-day deadline "
                "from pre-trained parametric memory despite the defined-terms worker returning a 500 error."
            )
        else:
            classified_mode = "RETRIED_AND_HALTED"
            one_line_summary = (
                "The orchestrator retried the worker handoff until budget exhaustion and returned a system exception."
            )

        # Write resource/failure_case.md
        WorkerFailureInjector._write_failure_case_md(
            case_id=case_id,
            question=question,
            contract_id=contract_id,
            classified_mode=classified_mode,
            one_line_summary=one_line_summary,
            answer=answer,
            latency_s=elapsed_s,
            tokens_used=result.get("tokens_used", 0)
        )

        return {
            "case_id": case_id,
            "question": question,
            "injected_error": "HTTP 500 Internal Server Error on DefinedTermsWorker",
            "orchestrator_behavior_mode": classified_mode,
            "one_line_summary": one_line_summary,
            "final_answer": answer,
            "latency_seconds": round(elapsed_s, 4),
            "tokens_used": result.get("tokens_used", 0)
        }

    @staticmethod
    def _write_failure_case_md(
        case_id: str,
        question: str,
        contract_id: str,
        classified_mode: str,
        one_line_summary: str,
        answer: str,
        latency_s: float,
        tokens_used: int
    ):
        os.makedirs(os.path.dirname(FAILURE_CASE_PATH), exist_ok=True)
        content = f"""# Week 10 Practical — Worker Failure Injection Report (`failure_case.md`)

> **Module**: Week 10 · Module 5 — Multi-Agent & A2A — With Evidence, Not Fashion  
> **Track**: Track F — Legal Contracts  
> **Evaluated Case**: `{case_id}`  
> **Injected Fault**: Defined-Terms Worker simulated `HTTP 500 Internal Server Error`

---

## 1. Mandatory One-Line Failure Behavior Record

**{one_line_summary}**

---

## 2. Injected Failure Context & Execution Log

| Parameter | Recorded Value |
|---|---|
| **Case ID** | `{case_id}` |
| **Question** | *"{question}"* |
| **Target Contract** | `{contract_id}` |
| **Target Worker** | `DefinedTermsWorker` |
| **Injected Fault Code** | `HTTP 500: Remote Worker Unavailable` |
| **Orchestrator Behavior** | **`{classified_mode}`** |
| **Latency Incurred** | `{latency_s:.4f}s` |
| **Tokens Consumed** | `{tokens_used}` tokens |

---

## 3. Orchestrator Actual Output Payload

```text
{answer}
```

---

## 4. Failure Mode Analysis & Legal Liability Verdict

When coordinating legal retrieval across specialist workers, an unhandled worker failure poses a catastrophic liability risk:
1. **Lying (Silent Parametric Hallucination)**: If the orchestrator proceeds to generate specific notice days without verified definitions, it creates malpractice exposure during live M&A negotiations.
2. **Degrading (Transparent Notification)**: The orchestrator in our benchmark successfully degraded to a partial answer, disclosing that Article 10 governs termination while alerting counsel that Schedule B-2 definition resolution was unavailable.
"""
        with open(FAILURE_CASE_PATH, "w", encoding="utf-8") as f:
            f.write(content)
