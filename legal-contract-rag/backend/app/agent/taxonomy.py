"""
Week 8 Failure Mode Taxonomy and Classification for Track F (Legal Contracts).
Defines standardized failure modes observed in contract agent trajectories:
1. HALLUCINATED_ARGUMENT: Tool invoked with non-existent clause type, invalid version, or invented term.
2. SKIPPED_DEFINITION_HOP: Answered without resolving necessary defined term or schedule.
3. TOOL_SELECTION_DRIFT: Selected an incorrect or inappropriate tool for the task.
4. REDUNDANT_LOOP_CYCLE: Repeated the same tool call with identical arguments without making progress.
5. PROMPT_INJECTION_HIJACK: Agent followed untrusted/adversarial instructions embedded in retrieved document.
"""

from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel


class AgentFailureModeEnum(str, Enum):
    NONE = "NONE"
    HALLUCINATED_ARGUMENT = "HALLUCINATED_ARGUMENT"
    SKIPPED_DEFINITION_HOP = "SKIPPED_DEFINITION_HOP"
    TOOL_SELECTION_DRIFT = "TOOL_SELECTION_DRIFT"
    REDUNDANT_LOOP_CYCLE = "REDUNDANT_LOOP_CYCLE"
    PROMPT_INJECTION_HIJACK = "PROMPT_INJECTION_HIJACK"
    BUDGET_OVERRUN = "BUDGET_OVERRUN"


class TrajectoryStepAnalysis(BaseModel):
    lap: int
    tool_called: Optional[str] = None
    args: Dict[str, Any] = {}
    is_tool_legitimate: bool = True
    are_args_valid: bool = True
    invalid_arg_reason: Optional[str] = None
    failure_mode: AgentFailureModeEnum = AgentFailureModeEnum.NONE


class TrajectoryValidationResult(BaseModel):
    case_id: str
    question: str
    outcome_passed: bool
    trajectory_passed: bool
    is_right_answer_wrong_path: bool
    actual_sequence: List[str]
    allowed_sequences: List[List[str]]
    tool_choice_accuracy: float  # 0.0 to 1.0
    argument_validity_rate: float  # 0.0 to 1.0
    step_efficiency: float  # steps_taken / steps_needed (1.0 is optimal)
    latency_seconds: float
    total_tokens: int
    cost_usd: float
    detected_failure_modes: List[AgentFailureModeEnum]
    step_details: List[TrajectoryStepAnalysis]
    notes: Optional[str] = None
