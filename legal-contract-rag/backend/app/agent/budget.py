"""
Runtime Budget Tracker for Week 7 Practical (Track F - Legal Contracts).
Enforces all 4 mandatory operational budgets:
1. MAX_ITERATIONS: Lap step limit
2. MAX_TOKENS: Cumulative tokens summed across EVERY lap
3. MAX_COST: Cumulative financial cost ($)
4. WALL_CLOCK: Maximum allowed elapsed execution time (seconds)
"""

import time
import logging
from typing import Optional, Dict, Any, Tuple
from backend.app.agent.enums import BudgetExceededReason

logger = logging.getLogger("budget_tracker")

# Default Pricing Rates per 1,000 tokens (Standard enterprise LLM rate)
DEFAULT_INPUT_COST_PER_1K = 0.00015   # $0.15 per 1M prompt tokens
DEFAULT_OUTPUT_COST_PER_1K = 0.00060  # $0.60 per 1M completion tokens


class BudgetTracker:
    """
    Monitors and enforces all four operational budgets during loop execution.
    Calculates cumulative token counts (summed on every lap) and cumulative cost.
    """

    def __init__(
        self,
        max_iterations: int = 5,
        max_tokens: int = 8000,
        max_cost_usd: float = 0.05,
        max_wall_clock_seconds: float = 20.0,
        input_cost_per_1k: float = DEFAULT_INPUT_COST_PER_1K,
        output_cost_per_1k: float = DEFAULT_OUTPUT_COST_PER_1K,
    ):
        self.max_iterations = max_iterations
        self.max_tokens = max_tokens
        self.max_cost_usd = max_cost_usd
        self.max_wall_clock_seconds = max_wall_clock_seconds
        self.input_cost_per_1k = input_cost_per_1k
        self.output_cost_per_1k = output_cost_per_1k

        self.iterations = 0
        self.cumulative_prompt_tokens = 0
        self.cumulative_completion_tokens = 0
        self.cumulative_total_tokens = 0
        self.cumulative_cost_usd = 0.0

        self.start_time = time.monotonic()
        self.end_time: Optional[float] = None
        self.exceeded_reason: Optional[BudgetExceededReason] = None

    @property
    def elapsed_seconds(self) -> float:
        current = self.end_time or time.monotonic()
        return current - self.start_time

    def record_lap(
        self,
        prompt_tokens: int,
        completion_tokens: int,
        explicit_cost: Optional[float] = None
    ) -> None:
        """
        Records resource consumption for a single loop iteration.
        Accumulates token totals and computes progressive dollar cost.
        """
        self.iterations += 1
        self.cumulative_prompt_tokens += prompt_tokens
        self.cumulative_completion_tokens += completion_tokens
        lap_total = prompt_tokens + completion_tokens
        self.cumulative_total_tokens += lap_total

        if explicit_cost is not None:
            self.cumulative_cost_usd += explicit_cost
        else:
            lap_cost = (
                (prompt_tokens / 1000.0) * self.input_cost_per_1k
                + (completion_tokens / 1000.0) * self.output_cost_per_1k
            )
            self.cumulative_cost_usd += lap_cost

        logger.debug(
            f"[BUDGET_LAP {self.iterations}] Lap Tokens: +{lap_total} | "
            f"Cumul Tokens: {self.cumulative_total_tokens}/{self.max_tokens} | "
            f"Cumul Cost: ${self.cumulative_cost_usd:.6f}/${self.max_cost_usd:.4f} | "
            f"Elapsed: {self.elapsed_seconds:.2f}s/{self.max_wall_clock_seconds:.1f}s"
        )

    def check_budget(self) -> Optional[BudgetExceededReason]:
        """
        Evaluates all four budgets against current execution metrics.
        Returns the specific BudgetExceededReason if a threshold was breached.
        """
        # 1. Iterations Check
        if self.iterations >= self.max_iterations:
            self.exceeded_reason = BudgetExceededReason.MAX_ITERATIONS
            return self.exceeded_reason

        # 2. Token Limit Check
        if self.cumulative_total_tokens >= self.max_tokens:
            self.exceeded_reason = BudgetExceededReason.MAX_TOKENS
            return self.exceeded_reason

        # 3. Dollar Cost Check
        if self.cumulative_cost_usd >= self.max_cost_usd:
            self.exceeded_reason = BudgetExceededReason.MAX_COST
            return self.exceeded_reason

        # 4. Wall Clock Elapsed Time Check
        if self.elapsed_seconds >= self.max_wall_clock_seconds:
            self.exceeded_reason = BudgetExceededReason.WALL_CLOCK_TIMEOUT
            return self.exceeded_reason

        return None

    def finalize(self) -> Dict[str, Any]:
        """Stops the clock and returns structured metrics snapshot."""
        if self.end_time is None:
            self.end_time = time.monotonic()
        return self.get_summary()

    def get_summary(self) -> Dict[str, Any]:
        return {
            "iterations": self.iterations,
            "max_iterations": self.max_iterations,
            "cumulative_prompt_tokens": self.cumulative_prompt_tokens,
            "cumulative_completion_tokens": self.cumulative_completion_tokens,
            "cumulative_total_tokens": self.cumulative_total_tokens,
            "max_tokens": self.max_tokens,
            "cumulative_cost_usd": round(self.cumulative_cost_usd, 6),
            "max_cost_usd": self.max_cost_usd,
            "elapsed_seconds": round(self.elapsed_seconds, 3),
            "max_wall_clock_seconds": self.max_wall_clock_seconds,
            "budget_exceeded": self.exceeded_reason is not None,
            "exceeded_reason": self.exceeded_reason.value if self.exceeded_reason else None,
        }

    def log_clean_termination(self) -> str:
        """Emits structured clean termination log event."""
        summary = self.get_summary()
        msg = (
            f"[BUDGET_TERMINATION_EVENT] Clean early exit triggered by {self.exceeded_reason.value}!\n"
            f"  - Iterations reached: {summary['iterations']}/{summary['max_iterations']}\n"
            f"  - Cumulative tokens: {summary['cumulative_total_tokens']}/{summary['max_tokens']}\n"
            f"  - Cumulative cost: ${summary['cumulative_cost_usd']:.6f}/${summary['max_cost_usd']:.4f}\n"
            f"  - Elapsed wall-clock: {summary['elapsed_seconds']:.3f}s/{summary['max_wall_clock_seconds']:.1f}s\n"
            f"  - State: TERMINATED_CLEANLY (zero infinite spinning)"
        )
        logger.warning(msg)
        return msg
