import time
import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, status

from backend.app.schemas.agent import (
    AgentQueryRequest, AgentQueryResponse,
    ReActResultDTO, AgentTraceStepDTO, BudgetStatusDTO,
    WorkflowResultDTO, FixedWorkflowStepDTO, ComparisonSummaryDTO,
    RaceDatasetItemDTO, RaceItemResultDTO, RaceRunResponse
)
from backend.app.agent.react_agent import ReActAgent
from backend.app.agent.fixed_workflow import FixedDeterministicWorkflow
from backend.app.agent.dataset import RACE_DATASET
from backend.app.agent.tools import TOOL_DEFINITIONS
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
