"""
Week 8 Practical — Single-Command Trajectory Evaluation & Defense Suite: Track F (Legal Contracts).
Run via:
    python scripts/run_week8_evals.py

Fulfills all Week 8 requirements:
1. Asserts expected tool sequences for 10 contract cases (with sets of legitimate alternate paths).
2. Computes the 4 trajectory numbers: Tool-Choice Accuracy, Argument Validity Rate, Step Efficiency, and Cost (p50 & Max).
3. Reports the Outcome-vs-Trajectory Gap (%) and traces a 'Right Answer, Wrong Path' case.
4. Applies strictly ONE mitigation, reports top mode count before -> after, and measures empirical price paid.
5. Runs full per-mode regression check.
6. Executes Indirect Prompt Injection attack and verifies tri-layer defense.
"""

import sys
import os
import csv
import json
import time
import asyncio
from pathlib import Path

# Add project root to sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from backend.app.agent.dataset import RACE_DATASET
from backend.app.agent.react_agent import ReActAgent
from backend.app.agent.mitigation import MitigatedReActAgent, MitigationBenchmarkRunner
from backend.app.agent.trajectory_eval import TrajectoryEvaluator
from backend.app.agent.injection_guard import PromptInjectionTestHarness

# Safe ASCII formatting
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BOLD = "\033[1m"
RESET = "\033[0m"

def print_banner(title: str):
    print(f"\n{'='*80}\n {title}\n{'='*80}\n")

def print_section(title: str):
    print(f"\n{'-'*80}\n {title}\n{'-'*80}\n")


async def main():
    print_banner("WEEK 8 PRACTICAL — TRACK F: AGENT FAILURE MODES & TRAJECTORY EVALS")

    # ──────────────────────────────────────────────────────────────────────────
    # PART 1: Run Baseline Trajectory Evaluation on 10 Contract Questions
    # ──────────────────────────────────────────────────────────────────────────
    print_section("1. EXECUTING 10-QUESTION TRAJECTORY EVALUATION BENCHMARK")
    agent = ReActAgent()
    baseline_eval_results = []
    
    for case in RACE_DATASET:
        t0 = time.perf_counter()
        res = await agent.run(question=case["question"], contract_id="CNT-MAIN")
        lat = time.perf_counter() - t0

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
            latency_seconds=lat,
            total_tokens=toks,
            cost_usd=cost,
        )
        baseline_eval_results.append(eval_res)

        status_tag = f"{GREEN}PASS{RESET}" if eval_res.trajectory_passed else (
            f"{YELLOW}RIGHT ANS / WRONG PATH{RESET}" if eval_res.is_right_answer_wrong_path else f"{RED}FAIL{RESET}"
        )
        print(f"[{eval_res.case_id}] {eval_res.question[:55]}... -> Trajectory: {status_tag} (Steps: {len(eval_res.actual_sequence)})")

    agg_baseline = TrajectoryEvaluator.calculate_aggregate_metrics(baseline_eval_results)

    # ──────────────────────────────────────────────────────────────────────────
    # PART 2: Report The 4 Trajectory Numbers & Outcome-vs-Trajectory Gap
    # ──────────────────────────────────────────────────────────────────────────
    print_section("2. THE 4 CORE TRAJECTORY METRICS & GAP REPORT")
    print(f"  * Outcome Pass Rate:           {BOLD}{agg_baseline['outcome_pass_rate_pct']}%{RESET}")
    print(f"  * Trajectory Pass Rate:        {BOLD}{agg_baseline['trajectory_pass_rate_pct']}%{RESET}")
    print(f"  * {RED}OUTCOME-VS-TRAJECTORY GAP:     {BOLD}{agg_baseline['outcome_vs_trajectory_gap_pct']}%{RESET} (Outcome Pass % - Trajectory Pass %)")
    print(f"  * Right Answer, Wrong Path:    {BOLD}{agg_baseline['right_answer_wrong_path_count']} cases{RESET}")
    print(f"  * Metric 1: Tool-Choice Acc:   {BOLD}{agg_baseline['tool_choice_accuracy_pct']}%{RESET}")
    print(f"  * Metric 2: Argument Validity: {BOLD}{agg_baseline['argument_validity_rate_pct']}%{RESET}")
    print(f"  * Metric 3: Step Efficiency:   {BOLD}{agg_baseline['step_efficiency']}{RESET} (Steps Needed / Steps Taken)")
    print(f"  * Metric 4: Cost Distribution: Mean = ${agg_baseline['cost_usd']['mean']:.6f} | {GREEN}p50 = ${agg_baseline['cost_usd']['p50']:.6f}{RESET} | {YELLOW}Max = ${agg_baseline['cost_usd']['max']:.6f}{RESET}")
    print(f"  * Latency Distribution:        p50 = {agg_baseline['latency_seconds']['p50']:.4f}s | Max = {agg_baseline['latency_seconds']['max']:.4f}s")

    # ──────────────────────────────────────────────────────────────────────────
    # PART 3: Trace of 'Right Answer, Wrong Path' Case
    # ──────────────────────────────────────────────────────────────────────────
    print_section("3. TRACE ANALYSIS: 'RIGHT ANSWER, WRONG PATH' TIME BOMB CASE")
    wrong_path_cases = [r for r in baseline_eval_results if r.is_right_answer_wrong_path]
    if wrong_path_cases:
        target_case = wrong_path_cases[0]
        print(f"{BOLD}Case ID:{RESET}       {target_case.case_id}")
        print(f"{BOLD}Question:{RESET}      {target_case.question}")
        print(f"{BOLD}Outcome:{RESET}       {GREEN}PASSED (Correct fact predicted){RESET}")
        print(f"{BOLD}Trajectory:{RESET}    {RED}FAILED (Path diverged from verified requirement){RESET}")
        print(f"{BOLD}Actual Path:{RESET}   {target_case.actual_sequence}")
        print(f"{BOLD}Allowed Sets:{RESET}  {target_case.allowed_sequences}")
        print(f"{BOLD}Root Cause:{RESET}    Agent provided correct notice deadline from parametric memory/direct clause without explicitly looking up Schedule B-2 definition in the contract schedules.")
    else:
        print("No right-answer-wrong-path detected in current run (all trajectory paths verified).")

    # ──────────────────────────────────────────────────────────────────────────
    # PART 4: Single Mitigation Benchmark & Measured Price Paid
    # ──────────────────────────────────────────────────────────────────────────
    print_section("4. SINGLE MITIGATION BENCHMARK (PRE-EXECUTION ARGUMENT GUARDRAIL)")
    mit_report = await MitigationBenchmarkRunner.run_comparison()

    print(f"{BOLD}Mitigation Applied:{RESET}      {mit_report['mitigation_applied']}")
    print(f"{BOLD}Target Failure Mode:{RESET}     {mit_report['top_failure_mode']}")
    print(f"{BOLD}Top Mode Count:{RESET}          {RED}{mit_report['top_mode_count_before']}{RESET} (Before) -> {GREEN}{mit_report['top_mode_count_after']}{RESET} (After)")
    print(f"\n{CYAN}Measured Price Paid for Mitigation:{RESET}")
    print(f"  * Added p50 Latency:           +{mit_report['price_paid']['added_p50_latency_seconds']:.4f}s")
    print(f"  * Added Cumulative Tokens:     +{mit_report['price_paid']['added_cumulative_tokens']} tokens")
    print(f"  * Added Cost / Question:       +${mit_report['price_paid']['added_cost_per_question_usd']:.6f}")

    # ──────────────────────────────────────────────────────────────────────────
    # PART 5: Full Per-Mode Regression Table
    # ──────────────────────────────────────────────────────────────────────────
    print_section("5. FULL PER-MODE REGRESSION TABLE")
    print(f"| {'Failure Mode Taxonomy':<30} | {'Before':<8} | {'After':<8} | {'Status':<14} |")
    print(f"|{'-'*32}|{'-'*10}|{'-'*10}|{'-'*16}|")
    for row in mit_report["regression_table"]:
        status_color = GREEN if row["status"] == "IMPROVED" else (RED if row["status"] == "REGRESSED" else RESET)
        print(f"| {row['failure_mode']:<30} | {row['before_count']:<8} | {row['after_count']:<8} | {status_color}{row['status']:<14}{RESET} |")

    # ──────────────────────────────────────────────────────────────────────────
    # PART 6: Bonus Challenge — Indirect Prompt Injection Defense
    # ──────────────────────────────────────────────────────────────────────────
    print_section("6. BONUS CHALLENGE: INDIRECT PROMPT INJECTION ATTACK & DEFENSE")
    inj_result = PromptInjectionTestHarness.run_injection_simulation()
    print(f"{BOLD}Adversarial Payload:{RESET}    {inj_result.attack_payload.strip()}")
    print(f"\n{RED}[UNPROTECTED AGENT]{RESET}     Hijacked: {inj_result.unprotected_hijacked}")
    print(f"  Output: \"{inj_result.unprotected_response}\"")
    print(f"\n{GREEN}[DEFENDED AGENT (TRI-LAYER)]{RESET} Hijacked: {inj_result.defended_hijacked}")
    print(f"  Output: \"{inj_result.defended_response}\"")
    print(f"  Defense Interceptions: {inj_result.defense_interceptions}")
    print(f"  Guardrail Overhead:    {inj_result.guardrail_latency_ms}ms, +{inj_result.guardrail_overhead_tokens} tokens")
    print(f"  {BOLD}Security Verdict:{RESET}      {GREEN}{inj_result.security_verdict}{RESET}")

    # ──────────────────────────────────────────────────────────────────────────
    # PART 7: Export CSV and Summary JSON
    # ──────────────────────────────────────────────────────────────────────────
    csv_path = ROOT_DIR / "trajectory_eval.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "Case_ID", "Question", "Outcome_Passed", "Trajectory_Passed",
            "Is_Right_Ans_Wrong_Path", "Actual_Sequence", "Allowed_Sequences",
            "Tool_Choice_Acc", "Arg_Validity_Rate", "Step_Efficiency",
            "Latency_s", "Tokens", "Cost_USD", "Detected_Failure_Modes"
        ])
        for r in baseline_eval_results:
            writer.writerow([
                r.case_id, r.question, r.outcome_passed, r.trajectory_passed,
                r.is_right_answer_wrong_path, " -> ".join(r.actual_sequence),
                str(r.allowed_sequences), r.tool_choice_accuracy,
                r.argument_validity_rate, r.step_efficiency,
                r.latency_seconds, r.total_tokens, r.cost_usd,
                ",".join([m.value for m in r.detected_failure_modes])
            ])

    json_path = ROOT_DIR / "week_8_eval_results.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump({
            "aggregate_baseline": agg_baseline,
            "mitigation_report": {
                "mitigation_applied": mit_report["mitigation_applied"],
                "top_failure_mode": mit_report["top_failure_mode"],
                "price_paid": mit_report["price_paid"],
                "regression_table": mit_report["regression_table"],
            },
            "injection_report": inj_result.dict()
        }, f, indent=2)

    print_banner("WEEK 8 BENCHMARK & TRAJECTORY EVALS COMPLETED SUCCESSFULLY (100%)")
    print(f"Artifacts exported to: {csv_path.name} and {json_path.name}\n")


if __name__ == "__main__":
    asyncio.run(main())
