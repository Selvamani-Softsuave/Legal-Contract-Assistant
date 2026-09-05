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
