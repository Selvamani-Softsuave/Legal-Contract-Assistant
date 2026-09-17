"""
Unit and Integration Tests for Week 8 Practical (Track F - Legal Contracts).
Tests:
1. Expected tool sequences for 10 contract cases with sets of allowed alternate paths.
2. 4 Trajectory numbers: Tool-choice accuracy, argument validity, step efficiency, and cost variance (p50 & max).
3. Outcome-vs-Trajectory gap computation and 'Right Answer, Wrong Path' detection.
4. Single mitigation before -> after top mode count and measured price paid.
5. Regression table safety across all taxonomy modes.
6. Indirect prompt injection attack neutralization via tri-layer defense.
"""

import sys
from pathlib import Path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import pytest
import asyncio
from backend.app.agent.dataset import RACE_DATASET
from backend.app.agent.react_agent import ReActAgent
from backend.app.agent.mitigation import MitigatedReActAgent, MitigationBenchmarkRunner, ArgumentValidationGuardrail
from backend.app.agent.trajectory_eval import TrajectoryEvaluator
from backend.app.agent.taxonomy import AgentFailureModeEnum
from backend.app.agent.injection_guard import PromptInjectionTestHarness, IndirectInjectionGuard


def test_dataset_contains_allowed_sequence_sets():
    """Verify that all 10 cases have allowed sequence sets supporting legitimate alternate paths."""
    assert len(RACE_DATASET) == 10
    for case in RACE_DATASET:
        assert "allowed_tool_sequences" in case
        assert isinstance(case["allowed_tool_sequences"], list)
        assert len(case["allowed_tool_sequences"]) >= 1
        assert "min_steps_needed" in case
        assert case["min_steps_needed"] >= 1


def test_argument_validation_guardrail():
    """Verify pre-execution guardrail catches hallucinated clause types and terms."""
    # Valid call
    is_valid, sanitized, err = ArgumentValidationGuardrail.sanitize_and_validate(
        "get_clause", {"clause_type": "TERMINATION"}
    )
    assert is_valid is True
    assert sanitized["clause_type"] == "TERMINATION"
    assert err is None

    # Hallucinated clause type
    is_valid, sanitized, err = ArgumentValidationGuardrail.sanitize_and_validate(
        "get_clause", {"clause_type": "NON_EXISTENT_SECTION_99"}
    )
    assert is_valid is False
    assert "Invalid clause_type" in err


@pytest.mark.asyncio
async def test_trajectory_evaluator_metrics():
    """Verify computation of the 4 trajectory metrics, cost p50/max, and gap."""
    agent = ReActAgent()
    eval_results = []
    
    for case in RACE_DATASET:
        res = await agent.run(question=case["question"], contract_id="CNT-MAIN")
        budget_info = res.get("metrics") or res.get("budget", {})
        toks = budget_info.get("cumulative_total_tokens") or budget_info.get("total_tokens", 0)
        cost = budget_info.get("cumulative_cost_usd") or budget_info.get("total_cost_usd", 0.0)
        trace = res.get("trace", [])
        ans = res.get("answer") or res.get("final_answer", "")

        if case["category"] == "BUDGET_STRESS_CIRCULAR":
            outcome_pass = "BUDGET_TERMINATION" in ans or "MAX_ITERATIONS" in ans or budget_info.get("budget_exceeded") is not None
        else:
            outcome_pass = any(fact.lower() in ans.lower() for fact in case["expected_facts"])

        eval_res = TrajectoryEvaluator.evaluate_case_trajectory(
            case_data=case,
            actual_trace_steps=trace,
            outcome_passed=outcome_pass,
            latency_seconds=0.01,
            total_tokens=toks,
            cost_usd=cost,
        )
        eval_results.append(eval_res)

    agg = TrajectoryEvaluator.calculate_aggregate_metrics(eval_results)

    # Assert 4 core metrics exist and are within valid bounds
    assert agg["total_cases"] == 10
    assert 0.0 <= agg["tool_choice_accuracy_pct"] <= 100.0
    assert 0.0 <= agg["argument_validity_rate_pct"] <= 100.0
    assert 0.0 <= agg["step_efficiency"] <= 1.0
    assert agg["cost_usd"]["p50"] >= 0.0
    assert agg["cost_usd"]["max"] >= agg["cost_usd"]["p50"]
    assert agg["outcome_pass_rate_pct"] >= agg["trajectory_pass_rate_pct"]
    assert agg["outcome_vs_trajectory_gap_pct"] >= 0.0


@pytest.mark.asyncio
async def test_mitigation_benchmark_runner():
    """Verify single mitigation execution, price tag measurement, and regression table."""
    report = await MitigationBenchmarkRunner.run_comparison()
    
    assert "mitigation_applied" in report
    assert "top_failure_mode" in report
    assert "price_paid" in report
    assert "added_p50_latency_seconds" in report["price_paid"]
    assert "added_cumulative_tokens" in report["price_paid"]
    assert "added_cost_per_question_usd" in report["price_paid"]
    assert len(report["regression_table"]) >= 5


def test_indirect_prompt_injection_defense():
    """Verify prompt injection exploit succeeds unprotected and is neutralized by tri-layer guardrail."""
    res = PromptInjectionTestHarness.run_injection_simulation()
    
    assert res.unprotected_hijacked is True
    assert res.defended_hijacked is False
    assert len(res.defense_interceptions) >= 1
    assert "ATTACK_NEUTRALIZED" in res.security_verdict
    assert res.guardrail_latency_ms >= 0.0
    assert res.guardrail_overhead_tokens > 0
