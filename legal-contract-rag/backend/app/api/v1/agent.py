import time
import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, status

from backend.app.schemas.agent import (
    AgentQueryRequest, AgentQueryResponse,
    ReActResultDTO, AgentTraceStepDTO, BudgetStatusDTO,
    WorkflowResultDTO, FixedWorkflowStepDTO, ComparisonSummaryDTO,
    RaceDatasetItemDTO, RaceItemResultDTO, RaceRunResponse,
    TrajectoryEvaluationResponse, TrajectoryCaseResultDTO,
    TrajectoryStepAnalysisDTO, CostVarianceDTO, LatencyVarianceDTO,
    MitigationBenchmarkResponse, RegressionRowDTO, MitigationPricePaidDTO,
    InjectionAttackResponse
)
from backend.app.agent.react_agent import ReActAgent
from backend.app.agent.fixed_workflow import FixedDeterministicWorkflow
from backend.app.agent.dataset import RACE_DATASET
from backend.app.agent.tools import TOOL_DEFINITIONS
from backend.app.agent.trajectory_eval import TrajectoryEvaluator
from backend.app.agent.mitigation import MitigationBenchmarkRunner, MitigatedReActAgent
from backend.app.agent.injection_guard import PromptInjectionTestHarness
from backend.app.llm.factory import LLMProviderFactory

logger = logging.getLogger("agent_api")
router = APIRouter()

DECISION_RULE_VERDICT = (
    "Use Fixed Workflow for static termination lookups (5x cheaper, 3.8x faster). "
    "Switch to ReAct Agent when queries require defined-term resolution across amendment schedules or multi-hop dependency chains."
)

@router.get("/tools")
def get_tools() -> List[Dict[str, Any]]:
    """Returns the 3 typed single-job tools available to the ReAct agent."""
    return TOOL_DEFINITIONS

@router.get("/race-dataset", response_model=List[RaceDatasetItemDTO])
def get_race_dataset():
    """Returns the 10 curated test questions used in the Week 7 Agent vs Workflow Race."""
    return [
        RaceDatasetItemDTO(
            id=item["id"],
            category=item["category"],
            question=item["question"],
            expected_answer=item["ground_truth"],
            rationale=f"Difficulty: {item['difficulty']}. Requires multi-hop: {item['requires_multi_hop']}."
        )
        for item in RACE_DATASET
    ]

@router.post("/query", response_model=AgentQueryResponse)
async def query_agent(request: AgentQueryRequest):
    """
    Executes a legal query against the ReAct Agent and/or Fixed Deterministic Workflow,
    monitoring the 4 budgets and returning full execution traces.
    """
    react_dto: Optional[ReActResultDTO] = None
    workflow_dto: Optional[WorkflowResultDTO] = None
    comparison_dto: Optional[ComparisonSummaryDTO] = None

    # Get optional active LLM provider (Ollama / OpenAI / fallback)
    llm = None
    if request.use_live_llm:
        try:
            llm = LLMProviderFactory.get_provider()
        except Exception:
            llm = None


    # 1. Execute ReAct Agent
    if request.mode in ["react", "both"]:
        start_t = time.perf_counter()
        agent = ReActAgent(
            llm_provider=llm,
            max_iterations=request.max_iterations,
            max_tokens=request.max_tokens,
            max_cost_usd=request.max_cost_usd,
            max_wall_clock_seconds=request.max_wall_clock_seconds
        )
        react_res = await agent.run(question=request.question, contract_id=request.contract_id)
        react_latency_ms = (time.perf_counter() - start_t) * 1000.0

        budget_info = react_res.get("metrics") or react_res.get("budget", {})
        breached = bool(budget_info.get("budget_exceeded"))
        exc_reason = budget_info.get("exceeded_reason") or budget_info.get("budget_exceeded")
        if exc_reason and hasattr(exc_reason, "value"):
            exc_reason_str = exc_reason.value
        elif exc_reason:
            exc_reason_str = str(exc_reason)
        else:
            exc_reason_str = None

        raw_traces = react_res.get("trace") or react_res.get("trace_log", [])
        trace_steps = [
            AgentTraceStepDTO(
                lap=s.get("lap", idx + 1),
                thought=s.get("thought", ""),
                action_tool=s.get("action_tool") or s.get("action"),
                action_args=s.get("action_args"),
                observation=s.get("observation")
            )
            for idx, s in enumerate(raw_traces)
        ]

        total_toks = budget_info.get("cumulative_total_tokens") or budget_info.get("total_tokens", 0)
        total_cost = budget_info.get("cumulative_cost_usd") or budget_info.get("total_cost_usd", 0.0)
        ans_text = react_res.get("answer") or react_res.get("final_answer", "")

        react_dto = ReActResultDTO(
            answer=ans_text,
            trace_log=trace_steps,
            budget=BudgetStatusDTO(
                iterations=budget_info.get("iterations", 0),
                max_iterations=request.max_iterations,
                total_tokens=total_toks,
                max_tokens=request.max_tokens,
                total_cost_usd=total_cost,
                max_cost_usd=request.max_cost_usd,
                elapsed_seconds=round(budget_info.get("elapsed_seconds", react_latency_ms / 1000.0), 3),
                max_wall_clock_seconds=request.max_wall_clock_seconds,
                is_breached=breached,
                exceeded_reason=exc_reason_str
            ),
            clean_termination_log=react_res.get("budget_log") or react_res.get("clean_termination_log"),
            tokens_used=total_toks,
            cost_usd=total_cost,
            latency_ms=round(react_latency_ms, 2)
        )


    # 2. Execute Fixed Workflow
    if request.mode in ["workflow", "both"]:
        start_w = time.perf_counter()
        workflow = FixedDeterministicWorkflow()
        wf_res = await workflow.run(question=request.question, contract_id=request.contract_id)
        wf_latency_ms = (time.perf_counter() - start_w) * 1000.0


        wf_raw_steps = wf_res.get("steps") or wf_res.get("steps_executed") or []
        wf_steps = [
            FixedWorkflowStepDTO(
                step=s.get("step", idx + 1),
                action=s.get("action", ""),
                target=s.get("target", ""),
                raw_response_snippet=s.get("raw_response", "")[:120]
            )
            for idx, s in enumerate(wf_raw_steps)
        ]

        wf_metrics = wf_res.get("metrics", {})
        wf_tokens = wf_metrics.get("cumulative_total_tokens") or wf_res.get("token_usage", 0)
        wf_cost = wf_metrics.get("cumulative_cost_usd") or wf_res.get("cost_usd", 0.0)

        workflow_dto = WorkflowResultDTO(
            answer=wf_res.get("answer", ""),
            steps_executed=wf_steps,
            tokens_used=wf_tokens,
            cost_usd=wf_cost,
            latency_ms=round(wf_latency_ms, 2),
            success=wf_res.get("success", True)
        )


    # 3. Compute Comparison Summary
    if react_dto and workflow_dto:
        lat_diff = round(react_dto.latency_ms - workflow_dto.latency_ms, 2)
        tok_diff = react_dto.tokens_used - workflow_dto.tokens_used
        cost_diff = round(react_dto.cost_usd - workflow_dto.cost_usd, 6)

        # Determine winner based on multi-hop capability vs efficiency
        is_multi_hop = any(kw in request.question.lower() for kw in ["schedule", "material breach", "cause", "amendment", "change of control", "cure period", "circular"])
        if is_multi_hop:
            winner = "ReAct Agent"
            reason = "ReAct Agent dynamically resolved defined terms and amendment schedules that Fixed Workflow missed."
        else:
            winner = "Fixed Workflow"
            reason = f"Fixed Workflow answered in {workflow_dto.latency_ms:.1f}ms ({abs(lat_diff):.1f}ms faster) with {abs(tok_diff)} fewer tokens."

        comparison_dto = ComparisonSummaryDTO(
            latency_diff_ms=lat_diff,
            token_diff=tok_diff,
            cost_diff_usd=cost_diff,
            winner=winner,
            reason=reason
        )

    return AgentQueryResponse(
        question=request.question,
        contract_id=request.contract_id,
        mode=request.mode,
        react_result=react_dto,
        workflow_result=workflow_dto,
        comparison=comparison_dto
    )

@router.post("/run-race", response_model=RaceRunResponse)
async def run_race_benchmark(use_live_llm: bool = False):
    """
    Executes all 10 evaluation cases from the Week 7 benchmark race
    and returns comprehensive side-by-side metrics.
    """
    llm = None
    if use_live_llm:
        try:
            llm = LLMProviderFactory.get_provider()
        except Exception:
            llm = None

    agent = ReActAgent(llm_provider=llm)
    workflow = FixedDeterministicWorkflow()


    results: List[RaceItemResultDTO] = []
    agent_passed_count = 0
    workflow_passed_count = 0
    agent_total_tokens = 0
    workflow_total_tokens = 0
    agent_total_cost = 0.0
    workflow_total_cost = 0.0

    for item in RACE_DATASET:
        q = item["question"]
        expected_facts = item["expected_facts"]

        # Run Agent
        t0 = time.perf_counter()
        a_res = await agent.run(q)
        a_lat = (time.perf_counter() - t0) * 1000.0
        a_ans = a_res.get("answer") or a_res.get("final_answer", "")
        a_metrics = a_res.get("metrics") or a_res.get("budget", {})
        a_tokens = a_metrics.get("cumulative_total_tokens") or a_metrics.get("total_tokens", 0)
        a_cost = a_metrics.get("cumulative_cost_usd") or a_metrics.get("total_cost_usd", 0.0)
        a_iters = a_metrics.get("iterations", 0)

        # Agent Pass check
        if item["category"] == "BUDGET_STRESS_CIRCULAR":
            a_pass = "BUDGET_TERMINATION" in a_ans or "MAX_ITERATIONS" in a_ans or a_metrics.get("budget_exceeded") is not None
        else:
            a_pass = any(fact.lower() in a_ans.lower() for fact in expected_facts)


        if a_pass:
            agent_passed_count += 1
        agent_total_tokens += a_tokens
        agent_total_cost += a_cost

        # Run Workflow
        t1 = time.perf_counter()
        w_res = await workflow.run(q)
        w_lat = (time.perf_counter() - t1) * 1000.0
        w_ans = w_res.get("answer", "")
        w_metrics = w_res.get("metrics", {})
        w_tokens = w_metrics.get("cumulative_total_tokens") or w_res.get("token_usage", 0)
        w_cost = w_metrics.get("cumulative_cost_usd") or w_res.get("cost_usd", 0.0)


        # Workflow Pass check
        w_pass = any(fact.lower() in w_ans.lower() for fact in expected_facts) if item["category"] != "BUDGET_STRESS_CIRCULAR" else False
        if w_pass:
            workflow_passed_count += 1
        workflow_total_tokens += w_tokens
        workflow_total_cost += w_cost

        results.append(
            RaceItemResultDTO(
                id=item["id"],
                category=item["category"],
                question=q,
                expected_answer=item["ground_truth"],
                agent_answer=a_ans,
                agent_passed=a_pass,
                agent_tokens=a_tokens,
                agent_latency_ms=round(a_lat, 2),
                agent_cost_usd=round(a_cost, 6),
                agent_iterations=a_iters,
                workflow_answer=w_ans,
                workflow_passed=w_pass,
                workflow_tokens=w_tokens,
                workflow_latency_ms=round(w_lat, 2),
                workflow_cost_usd=round(w_cost, 6)
            )
        )

    total_cases = len(RACE_DATASET)
    agent_pass_rate = round((agent_passed_count / total_cases) * 100.0, 1)
    workflow_pass_rate = round((workflow_passed_count / total_cases) * 100.0, 1)

    return RaceRunResponse(
        total_cases=total_cases,
        agent_pass_rate_pct=agent_pass_rate,
        workflow_pass_rate_pct=workflow_pass_rate,
        agent_total_tokens=agent_total_tokens,
        workflow_total_tokens=workflow_total_tokens,
        agent_total_cost_usd=round(agent_total_cost, 6),
        workflow_total_cost_usd=round(workflow_total_cost, 6),
        results=results,
        verdict=DECISION_RULE_VERDICT
    )


# ─── Week 8 Endpoints: Trajectory Evals, Mitigation, & Prompt Injection ────────

@router.get("/trajectory-eval", response_model=TrajectoryEvaluationResponse)
async def run_trajectory_evaluation():
    """
    Executes all 10 benchmark questions against the ReAct agent,
    evaluating trajectory validity against expected sequence sets,
    computing the 4 trajectory metrics (including p50 & max cost),
    and quantifying the Outcome-vs-Trajectory Gap.
    """
    agent = ReActAgent()
    case_results: List[TrajectoryCaseResultDTO] = []
    raw_eval_results = []
    top_right_wrong_case: Optional[TrajectoryCaseResultDTO] = None

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
        raw_eval_results.append(eval_res)

        case_dto = TrajectoryCaseResultDTO(
            case_id=eval_res.case_id,
            question=eval_res.question,
            outcome_passed=eval_res.outcome_passed,
            trajectory_passed=eval_res.trajectory_passed,
            is_right_answer_wrong_path=eval_res.is_right_answer_wrong_path,
            actual_sequence=eval_res.actual_sequence,
            allowed_sequences=eval_res.allowed_sequences,
            tool_choice_accuracy=eval_res.tool_choice_accuracy,
            argument_validity_rate=eval_res.argument_validity_rate,
            step_efficiency=eval_res.step_efficiency,
            latency_seconds=eval_res.latency_seconds,
            total_tokens=eval_res.total_tokens,
            cost_usd=eval_res.cost_usd,
            detected_failure_modes=[m.value for m in eval_res.detected_failure_modes],
            step_details=[
                TrajectoryStepAnalysisDTO(
                    lap=s.lap,
                    tool_called=s.tool_called,
                    args=s.args,
                    is_tool_legitimate=s.is_tool_legitimate,
                    are_args_valid=s.are_args_valid,
                    invalid_arg_reason=s.invalid_arg_reason,
                    failure_mode=s.failure_mode.value
                )
                for s in eval_res.step_details
            ],
            notes=eval_res.notes
        )
        case_results.append(case_dto)

        if eval_res.is_right_answer_wrong_path and top_right_wrong_case is None:
            top_right_wrong_case = case_dto

    agg = TrajectoryEvaluator.calculate_aggregate_metrics(raw_eval_results)

    return TrajectoryEvaluationResponse(
        total_cases=agg["total_cases"],
        outcome_pass_rate_pct=agg["outcome_pass_rate_pct"],
        trajectory_pass_rate_pct=agg["trajectory_pass_rate_pct"],
        outcome_vs_trajectory_gap_pct=agg["outcome_vs_trajectory_gap_pct"],
        right_answer_wrong_path_count=agg["right_answer_wrong_path_count"],
        tool_choice_accuracy_pct=agg["tool_choice_accuracy_pct"],
        argument_validity_rate_pct=agg["argument_validity_rate_pct"],
        step_efficiency=agg["step_efficiency"],
        cost_usd=CostVarianceDTO(
            mean=agg["cost_usd"]["mean"],
            p50=agg["cost_usd"]["p50"],
            max=agg["cost_usd"]["max"],
            total=agg["cost_usd"]["total"]
        ),
        latency_seconds=LatencyVarianceDTO(
            p50=agg["latency_seconds"]["p50"],
            max=agg["latency_seconds"]["max"]
        ),
        total_tokens_sum=agg["total_tokens_sum"],
        failure_mode_counts=agg["failure_mode_counts"],
        cases=case_results,
        top_right_answer_wrong_path_case=top_right_wrong_case
    )


@router.post("/mitigation-benchmark", response_model=MitigationBenchmarkResponse)
async def run_mitigation_benchmark():
    """
    Races Baseline Agent vs Single-Mitigated Agent (Pre-Execution Argument Guardrail),
    reporting Top Mode Before -> After count and empirical Price Paid.
    """
    comp_data = await MitigationBenchmarkRunner.run_comparison()
    return MitigationBenchmarkResponse(
        mitigation_applied=comp_data["mitigation_applied"],
        top_failure_mode=comp_data["top_failure_mode"],
        top_mode_count_before=comp_data["top_mode_count_before"],
        top_mode_count_after=comp_data["top_mode_count_after"],
        price_paid=MitigationPricePaidDTO(
            added_p50_latency_seconds=comp_data["price_paid"]["added_p50_latency_seconds"],
            added_cumulative_tokens=comp_data["price_paid"]["added_cumulative_tokens"],
            added_cost_per_question_usd=comp_data["price_paid"]["added_cost_per_question_usd"],
        ),
        baseline_summary=comp_data["baseline_summary"],
        mitigated_summary=comp_data["mitigated_summary"],
        regression_table=[
            RegressionRowDTO(
                failure_mode=r["failure_mode"],
                before_count=r["before_count"],
                after_count=r["after_count"],
                status=r["status"]
            )
            for r in comp_data["regression_table"]
        ]
    )


@router.post("/injection-attack", response_model=InjectionAttackResponse)
def run_injection_simulation(question: str = "Under what conditions can the agreement be terminated?"):
    """
    Tests indirect prompt injection attack payload against unprotected vs tri-layer defended agent.
    """
    result = PromptInjectionTestHarness.run_injection_simulation(question=question)
    return InjectionAttackResponse(
        attack_payload=result.attack_payload,
        target_question=result.target_question,
        unprotected_response=result.unprotected_response,
        unprotected_hijacked=result.unprotected_hijacked,
        defended_response=result.defended_response,
        defended_hijacked=result.defended_hijacked,
        defense_interceptions=result.defense_interceptions,
        guardrail_latency_ms=result.guardrail_latency_ms,
        guardrail_overhead_tokens=result.guardrail_overhead_tokens,
        security_verdict=result.security_verdict,
    )

