"""
Trajectory Evaluation Engine for Week 8 Practical (Track F - Legal Contracts).
Computes:
1. Tool-Choice Accuracy (%)
2. Argument Validity Rate (%) (Validates real vs fluent hallucinated arguments)
3. Step Efficiency (Steps Needed / Steps Taken)
4. Cost & Latency Distribution (Mean, p50, and Max)
5. Outcome-vs-Trajectory Gap (Outcome Pass Rate - Trajectory Pass Rate)
6. Identification of 'Right Answer, Wrong Path' Traces
"""

import statistics
import logging
from typing import List, Dict, Any, Optional, Tuple, Set

from backend.app.agent.taxonomy import (
    AgentFailureModeEnum,
    TrajectoryStepAnalysis,
    TrajectoryValidationResult,
)
from backend.app.agent.enums import ContractVersionEnum, ClauseTypeEnum
from backend.app.agent.dataset import RACE_DATASET
from backend.app.agent.tools import MOCK_CONTRACT_STORE, AVAILABLE_TOOLS

logger = logging.getLogger("trajectory_eval")

VALID_CLAUSE_TYPES = {c.value for c in ClauseTypeEnum}
VALID_VERSIONS = {v.value for v in ContractVersionEnum}
KNOWN_VALID_DEFINITIONS = {
    "CURE PERIOD", "MATERIAL BREACH", "NOTICE PERIOD", "APPLICABLE SCHEDULE",
    "SCHEDULE B-2", "BUSINESS DAY", "CHANGE OF CONTROL",
    "CIRCULAR TERM ALPHA", "CIRCULAR TERM BETA", "CIRCULAR TERM GAMMA"
}


class TrajectoryEvaluator:
    """
    Evaluates execution trajectories of the Legal Contract ReAct Agent.
    """

    @staticmethod
    def validate_tool_argument(tool_name: str, args: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Validates whether tool arguments are structurally and substantively valid,
        or represent fluent hallucinations / made-up keys.
        """
        if tool_name not in AVAILABLE_TOOLS:
            return False, f"Unknown tool name '{tool_name}'"

        if tool_name == "get_clause":
            clause_type = args.get("clause_type") or args.get("clause")
            if not clause_type:
                return False, "Missing required argument 'clause_type'"
            c_str = str(clause_type).upper().strip()
            if c_str not in VALID_CLAUSE_TYPES and not any(c in c_str for c in ["TERMINATION", "NOTICE", "GOVERNING", "LIABILITY"]):
                return False, f"Invalid or hallucinated clause_type '{clause_type}' (Expected: {sorted(list(VALID_CLAUSE_TYPES))})"

        elif tool_name == "get_definitions":
            term = args.get("term") or args.get("definition_term") or args.get("defined_term")
            if not term:
                return False, "Missing required argument 'term'"
            t_str = str(term).upper().strip()
            # Allow known terms or schedule references
            if t_str not in KNOWN_VALID_DEFINITIONS and "SCHEDULE" not in t_str and "CURE" not in t_str and "BREACH" not in t_str:
                return False, f"Hallucinated or non-existent defined term '{term}'"

        elif tool_name == "get_effective_date_and_metadata":
            # contract_id is optional with default
            pass

        # Validate version if provided
        ver = args.get("contract_version") or args.get("version")
        if ver:
            v_str = str(ver).upper().strip()
            if v_str not in VALID_VERSIONS and "FINAL" not in v_str and "AMENDMENT" not in v_str and "ORIGINAL" not in v_str:
                return False, f"Invalid contract_version '{ver}'"

        return True, None

    @classmethod
    def evaluate_case_trajectory(
        cls,
        case_data: Dict[str, Any],
        actual_trace_steps: List[Dict[str, Any]],
        outcome_passed: bool,
        latency_seconds: float,
        total_tokens: int,
        cost_usd: float,
    ) -> TrajectoryValidationResult:
        """
        Evaluates the trajectory of a single question run against dataset ground truth.
        """
        case_id = case_data["id"]
        question = case_data["question"]
        allowed_seqs = case_data.get("allowed_tool_sequences", [])
        min_steps_needed = max(1, case_data.get("min_steps_needed", 1))
        required_tools = case_data.get("required_tools", [])
        required_defs = [d.upper() for d in case_data.get("required_definitions", [])]

        step_analyses: List[TrajectoryStepAnalysis] = []
        actual_sequence: List[str] = []
        tools_called_set: Set[str] = set()
        resolved_definitions: Set[str] = set()
        detected_modes: List[AgentFailureModeEnum] = []

        valid_args_count = 0
        legitimate_tools_count = 0

        # Filter to only actual tool invocation steps
        tool_steps = []
        for step in actual_trace_steps:
            tool_name = step.get("action_tool")
            raw_action = step.get("action") or ""
            if not tool_name and "(" in raw_action:
                tool_name = raw_action.split("(", 1)[0].strip()

            if tool_name and tool_name not in ["FINAL_ANSWER", "TERMINATE_CLEANLY", "NONE", "TERMINATE"]:
                tool_steps.append((tool_name, step))

        total_tool_steps = len(tool_steps)

        for idx, (tool_name, step) in enumerate(tool_steps):
            lap = step.get("lap", idx + 1)
            args = step.get("action_args") or step.get("args") or {}
            if isinstance(args, str):
                try:
                    import json
                    args = json.loads(args)
                except Exception:
                    args = {}

            actual_sequence.append(tool_name)
            tools_called_set.add(tool_name)

            # 1. Tool-choice legitimacy
            is_legitimate_tool = tool_name in AVAILABLE_TOOLS
            if is_legitimate_tool:
                legitimate_tools_count += 1
            else:
                detected_modes.append(AgentFailureModeEnum.TOOL_SELECTION_DRIFT)

            # 2. Argument validity
            are_valid, invalid_reason = cls.validate_tool_argument(tool_name, args)
            if are_valid:
                valid_args_count += 1
                if tool_name == "get_definitions":
                    t = args.get("term") or args.get("definition_term") or ""
                    if t:
                        resolved_definitions.add(str(t).upper().strip())
            else:
                detected_modes.append(AgentFailureModeEnum.HALLUCINATED_ARGUMENT)

            step_analyses.append(
                TrajectoryStepAnalysis(
                    lap=lap,
                    tool_called=tool_name,
                    args=args,
                    is_tool_legitimate=is_legitimate_tool,
                    are_args_valid=are_valid,
                    invalid_arg_reason=invalid_reason,
                    failure_mode=(
                        AgentFailureModeEnum.HALLUCINATED_ARGUMENT if not are_valid
                        else (AgentFailureModeEnum.TOOL_SELECTION_DRIFT if not is_legitimate_tool
                              else AgentFailureModeEnum.NONE)
                    )
                )
            )

        # Compute Step-level metrics
        if total_tool_steps > 0:
            tool_choice_accuracy = round(legitimate_tools_count / total_tool_steps, 4)
            arg_validity_rate = round(valid_args_count / total_tool_steps, 4)
            step_efficiency = round(min(1.0, min_steps_needed / total_tool_steps), 4)
        else:
            tool_choice_accuracy = 1.0 if not required_tools else 0.0
            arg_validity_rate = 1.0
            step_efficiency = 1.0 if min_steps_needed == 0 else 0.0

        # Trajectory validity check against allowed sequence sets
        sequence_matches_allowed = False
        if not allowed_seqs and not actual_sequence:
            sequence_matches_allowed = True
        else:
            for allowed in allowed_seqs:
                if actual_sequence == allowed:
                    sequence_matches_allowed = True
                    break

        # Check required definitions
        missed_definitions = False
        for req_def in required_defs:
            if not any(req_def in d or d in req_def for d in resolved_definitions):
                missed_definitions = True
                detected_modes.append(AgentFailureModeEnum.SKIPPED_DEFINITION_HOP)
                break

        # Check redundant loops
        if len(actual_sequence) > len(set(actual_sequence)) and len(actual_sequence) >= 3:
            if case_data.get("category") != "BUDGET_STRESS_CIRCULAR":
                detected_modes.append(AgentFailureModeEnum.REDUNDANT_LOOP_CYCLE)

        # Overall trajectory pass criterion:
        # 1. Tool choice >= 100%
        # 2. Argument validity >= 100%
        # 3. Required definitions resolved
        # 4. Sequence matched one of the allowed alternate paths
        trajectory_passed = (
            sequence_matches_allowed and
            tool_choice_accuracy >= 1.0 and
            arg_validity_rate >= 1.0 and
            not missed_definitions
        )

        # Detect the crucial "Right Answer, Wrong Path"
        is_right_answer_wrong_path = bool(outcome_passed and not trajectory_passed)

        if not detected_modes:
            detected_modes.append(AgentFailureModeEnum.NONE)

        # Deduplicate failure modes preserving order
        dedup_modes = []
        for m in detected_modes:
            if m not in dedup_modes:
                dedup_modes.append(m)

        notes = None
        if is_right_answer_wrong_path:
            notes = f"Right answer reached via unverified path! Sequence took {actual_sequence}, expected one of {allowed_seqs}."

        return TrajectoryValidationResult(
            case_id=case_id,
            question=question,
            outcome_passed=outcome_passed,
            trajectory_passed=trajectory_passed,
            is_right_answer_wrong_path=is_right_answer_wrong_path,
            actual_sequence=actual_sequence,
            allowed_sequences=allowed_seqs,
            tool_choice_accuracy=tool_choice_accuracy,
            argument_validity_rate=arg_validity_rate,
            step_efficiency=step_efficiency,
            latency_seconds=round(latency_seconds, 4),
            total_tokens=total_tokens,
            cost_usd=round(cost_usd, 6),
            detected_failure_modes=dedup_modes,
            step_details=step_analyses,
            notes=notes
        )

    @classmethod
    def calculate_aggregate_metrics(
        cls,
        results: List[TrajectoryValidationResult]
    ) -> Dict[str, Any]:
        """
        Calculates aggregate 4 trajectory numbers, cost variance (p50 & max),
        and the Outcome-vs-Trajectory Gap.
        """
        if not results:
            return {}

        n = len(results)
        outcome_passes = sum(1 for r in results if r.outcome_passed)
        trajectory_passes = sum(1 for r in results if r.trajectory_passed)
        right_ans_wrong_paths = [r for r in results if r.is_right_answer_wrong_path]

        outcome_pass_rate = round((outcome_passes / n) * 100.0, 2)
        trajectory_pass_rate = round((trajectory_passes / n) * 100.0, 2)
        gap_number = round(outcome_pass_rate - trajectory_pass_rate, 2)

        tool_accuracies = [r.tool_choice_accuracy for r in results]
        arg_validities = [r.argument_validity_rate for r in results]
        efficiencies = [r.step_efficiency for r in results]
        costs = [r.cost_usd for r in results]
        latencies = [r.latency_seconds for r in results]
        tokens = [r.total_tokens for r in results]

        avg_tool_accuracy = round((sum(tool_accuracies) / n) * 100.0, 2)
        avg_arg_validity = round((sum(arg_validities) / n) * 100.0, 2)
        avg_step_efficiency = round((sum(efficiencies) / n), 4)

        # Cost stats
        mean_cost = round(statistics.mean(costs), 6)
        p50_cost = round(statistics.median(costs), 6)
        max_cost = round(max(costs), 6)

        # Latency stats
        p50_latency = round(statistics.median(latencies), 4)
        max_latency = round(max(latencies), 4)

        # Failure mode counts
        mode_counts: Dict[str, int] = {}
        for r in results:
            for m in r.detected_failure_modes:
                if m != AgentFailureModeEnum.NONE:
                    mode_counts[m.value] = mode_counts.get(m.value, 0) + 1

        return {
            "total_cases": n,
            "outcome_pass_rate_pct": outcome_pass_rate,
            "trajectory_pass_rate_pct": trajectory_pass_rate,
            "outcome_vs_trajectory_gap_pct": gap_number,
            "right_answer_wrong_path_count": len(right_ans_wrong_paths),
            "tool_choice_accuracy_pct": avg_tool_accuracy,
            "argument_validity_rate_pct": avg_arg_validity,
            "step_efficiency": avg_step_efficiency,
            "cost_usd": {
                "mean": mean_cost,
                "p50": p50_cost,
                "max": max_cost,
                "total": round(sum(costs), 6),
            },
            "latency_seconds": {
                "p50": p50_latency,
                "max": max_latency,
            },
            "total_tokens_sum": sum(tokens),
            "failure_mode_counts": mode_counts,
        }
