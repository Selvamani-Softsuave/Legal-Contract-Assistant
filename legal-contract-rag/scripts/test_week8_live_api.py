"""
Live End-to-End API Test Suite for Week 8 Trajectory Evaluation & Prompt Injection Defense.
Run via:
    python scripts/test_week8_live_api.py
"""

import sys
from pathlib import Path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BOLD = "\033[1m"
RESET = "\033[0m"

def print_header(title: str):
    print(f"\n{CYAN}{'='*75}\n {title}\n{'='*75}{RESET}")

def test_trajectory_eval_endpoint():
    print_header("TEST 1: GET /api/v1/agent/trajectory-eval")
    res = client.get("/api/v1/agent/trajectory-eval")
    assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
    data = res.json()
    
    assert data["total_cases"] == 10
    assert "outcome_pass_rate_pct" in data
    assert "trajectory_pass_rate_pct" in data
    assert "outcome_vs_trajectory_gap_pct" in data
    assert "tool_choice_accuracy_pct" in data
    assert "argument_validity_rate_pct" in data
    assert "step_efficiency" in data
    assert "cost_usd" in data
    assert "p50" in data["cost_usd"]
    assert "max" in data["cost_usd"]
    assert len(data["cases"]) == 10

    print(f"{GREEN}[PASS]{RESET} Trajectory Eval Endpoint Verified:")
    print(f"       Outcome Pass Rate:     {data['outcome_pass_rate_pct']}%")
    print(f"       Trajectory Pass Rate:  {data['trajectory_pass_rate_pct']}%")
    print(f"       Outcome-Trajectory Gap:{data['outcome_vs_trajectory_gap_pct']}%")
    print(f"       Cost p50:              ${data['cost_usd']['p50']:.6f} | Max: ${data['cost_usd']['max']:.6f}")


def test_mitigation_benchmark_endpoint():
    print_header("TEST 2: POST /api/v1/agent/mitigation-benchmark")
    res = client.post("/api/v1/agent/mitigation-benchmark")
    assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
    data = res.json()

    assert "mitigation_applied" in data
    assert "top_failure_mode" in data
    assert "price_paid" in data
    assert "added_p50_latency_seconds" in data["price_paid"]
    assert "added_cumulative_tokens" in data["price_paid"]
    assert "added_cost_per_question_usd" in data["price_paid"]
    assert len(data["regression_table"]) >= 5

    print(f"{GREEN}[PASS]{RESET} Mitigation Benchmark Endpoint Verified:")
    print(f"       Mitigation:         {data['mitigation_applied']}")
    print(f"       Top Mode Count:     {data['top_mode_count_before']} (Before) -> {data['top_mode_count_after']} (After)")
    print(f"       Price Paid Latency: +{data['price_paid']['added_p50_latency_seconds']:.4f}s")
    print(f"       Price Paid Cost/Q:  +${data['price_paid']['added_cost_per_question_usd']:.6f}")


def test_injection_attack_endpoint():
    print_header("TEST 3: POST /api/v1/agent/injection-attack")
    res = client.post("/api/v1/agent/injection-attack", params={"question": "Under what conditions can the agreement be terminated?"})
    assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
    data = res.json()

    assert data["unprotected_hijacked"] is True
    assert data["defended_hijacked"] is False
    assert len(data["defense_interceptions"]) >= 1
    assert "ATTACK_NEUTRALIZED" in data["security_verdict"]

    print(f"{GREEN}[PASS]{RESET} Prompt Injection Defense Endpoint Verified:")
    print(f"       Unprotected Hijacked: {data['unprotected_hijacked']}")
    print(f"       Defended Hijacked:    {data['defended_hijacked']}")
    print(f"       Security Verdict:     {data['security_verdict']}")
    print(f"       Defense Interceptions:{data['defense_interceptions']}")


if __name__ == "__main__":
    print_header("STARTING WEEK 8 LIVE FASTAPI END-TO-END TESTS")
    test_trajectory_eval_endpoint()
    test_mitigation_benchmark_endpoint()
    test_injection_attack_endpoint()
    print_header("ALL WEEK 8 LIVE API TESTS PASSED SUCCESSFULLY (100%)")
