from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from backend.app.agent.enums import ContractVersionEnum, BudgetExceededReason

class AgentQueryRequest(BaseModel):
    question: str = Field(..., description="Legal question to evaluate")
    contract_id: str = Field(default="CNT-MAIN", description="Contract ID identifier")
    mode: str = Field(default="both", description="Execution mode: 'react', 'workflow', or 'both'")
    use_live_llm: Optional[bool] = Field(default=None, description="Whether to invoke live LLM (e.g. Ollama) or calibrated agent loop")
    max_iterations: int = Field(default=5, ge=1, le=20, description="Max ReAct iterations")
    max_tokens: int = Field(default=8000, ge=100, le=100000, description="Max token budget")
    max_cost_usd: float = Field(default=0.05, ge=0.001, le=10.0, description="Max cost budget in USD")
    max_wall_clock_seconds: float = Field(default=20.0, ge=1.0, le=120.0, description="Max wall clock timeout in seconds")


class AgentTraceStepDTO(BaseModel):
    lap: int
    thought: str
    action_tool: Optional[str] = None
    action_args: Optional[Dict[str, Any]] = None
    observation: Optional[str] = None

class BudgetStatusDTO(BaseModel):
    iterations: int
    max_iterations: int
    total_tokens: int
    max_tokens: int
    total_cost_usd: float
    max_cost_usd: float
    elapsed_seconds: float
    max_wall_clock_seconds: float
    is_breached: bool
    exceeded_reason: Optional[str] = None

class ReActResultDTO(BaseModel):
    answer: str
    trace_log: List[AgentTraceStepDTO]
    budget: BudgetStatusDTO
    clean_termination_log: Optional[str] = None
    tokens_used: int
    cost_usd: float
    latency_ms: float

class FixedWorkflowStepDTO(BaseModel):
    step: int
    action: str
    target: str
    raw_response_snippet: str

class WorkflowResultDTO(BaseModel):
    answer: str
    steps_executed: List[FixedWorkflowStepDTO]
    tokens_used: int
    cost_usd: float
    latency_ms: float
    success: bool

class ComparisonSummaryDTO(BaseModel):
    latency_diff_ms: float
    token_diff: int
    cost_diff_usd: float
    winner: str
    reason: str

class AgentQueryResponse(BaseModel):
    question: str
    contract_id: str
    mode: str
    react_result: Optional[ReActResultDTO] = None
    workflow_result: Optional[WorkflowResultDTO] = None
    comparison: Optional[ComparisonSummaryDTO] = None

class RaceDatasetItemDTO(BaseModel):
    id: str
    category: str
    question: str
    expected_answer: str
    rationale: str

class RaceItemResultDTO(BaseModel):
    id: str
    category: str
    question: str
    expected_answer: str
    agent_answer: str
    agent_passed: bool
    agent_tokens: int
    agent_latency_ms: float
    agent_cost_usd: float
    agent_iterations: int
    workflow_answer: str
    workflow_passed: bool
    workflow_tokens: int
    workflow_latency_ms: float
    workflow_cost_usd: float

class RaceRunResponse(BaseModel):
    total_cases: int
    agent_pass_rate_pct: float
    workflow_pass_rate_pct: float
    agent_total_tokens: int
    workflow_total_tokens: int
    agent_total_cost_usd: float
    workflow_total_cost_usd: float
    results: List[RaceItemResultDTO]
    verdict: str


# ─── Week 8 Trajectory Evaluation & Defense DTOs ──────────────────────────────

class TrajectoryStepAnalysisDTO(BaseModel):
    lap: int
    tool_called: Optional[str] = None
    args: Dict[str, Any] = {}
    is_tool_legitimate: bool = True
    are_args_valid: bool = True
    invalid_arg_reason: Optional[str] = None
    failure_mode: str = "NONE"

class TrajectoryCaseResultDTO(BaseModel):
    case_id: str
    question: str
    outcome_passed: bool
    trajectory_passed: bool
    is_right_answer_wrong_path: bool
    actual_sequence: List[str]
    allowed_sequences: List[List[str]]
    tool_choice_accuracy: float
    argument_validity_rate: float
    step_efficiency: float
    latency_seconds: float
    total_tokens: int
    cost_usd: float
    detected_failure_modes: List[str]
    step_details: List[TrajectoryStepAnalysisDTO]
    notes: Optional[str] = None

class CostVarianceDTO(BaseModel):
    mean: float
    p50: float
    max: float
    total: float

class LatencyVarianceDTO(BaseModel):
    p50: float
    max: float

class TrajectoryEvaluationResponse(BaseModel):
    total_cases: int
    outcome_pass_rate_pct: float
    trajectory_pass_rate_pct: float
    outcome_vs_trajectory_gap_pct: float
    right_answer_wrong_path_count: int
    tool_choice_accuracy_pct: float
    argument_validity_rate_pct: float
    step_efficiency: float
    cost_usd: CostVarianceDTO
    latency_seconds: LatencyVarianceDTO
    total_tokens_sum: int
    failure_mode_counts: Dict[str, int]
    cases: List[TrajectoryCaseResultDTO]
    top_right_answer_wrong_path_case: Optional[TrajectoryCaseResultDTO] = None

class RegressionRowDTO(BaseModel):
    failure_mode: str
    before_count: int
    after_count: int
    status: str

class MitigationPricePaidDTO(BaseModel):
    added_p50_latency_seconds: float
    added_cumulative_tokens: int
    added_cost_per_question_usd: float

class MitigationBenchmarkResponse(BaseModel):
    mitigation_applied: str
    top_failure_mode: str
    top_mode_count_before: int
    top_mode_count_after: int
    price_paid: MitigationPricePaidDTO
    baseline_summary: Dict[str, Any]
    mitigated_summary: Dict[str, Any]
    regression_table: List[RegressionRowDTO]

class InjectionAttackResponse(BaseModel):
    attack_payload: str
    target_question: str
    unprotected_response: str
    unprotected_hijacked: bool
    defended_response: str
    defended_hijacked: bool
    defense_interceptions: List[str]
    guardrail_latency_ms: float
    guardrail_overhead_tokens: int
    security_verdict: str
