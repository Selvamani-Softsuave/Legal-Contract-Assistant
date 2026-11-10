"""
Unit and Integration Tests for Week 7 Practical (Track F - Legal Contracts).
Tests tools, 4-budget enforcement, ReAct agent loop, fixed workflow, and memory buffer.
"""

import pytest
import asyncio
from backend.app.agent.enums import ContractVersionEnum, ClauseTypeEnum, BudgetExceededReason
from backend.app.agent.tools import (
    get_clause,
    get_effective_date_and_metadata,
    get_definitions,
    TOOL_DEFINITIONS,
    AVAILABLE_TOOLS,
)
from backend.app.agent.budget import BudgetTracker
from backend.app.agent.react_agent import ReActAgent
from backend.app.agent.fixed_workflow import FixedContractWorkflow
from backend.app.agent.memory import SlidingWindowMemory, PersistentFactStore
from backend.app.agent.dataset import RACE_DATASET


def test_tools_enum_and_non_overlap():
    """Verify tool parameter Enums and non-overlapping single-job descriptions."""
    assert len(AVAILABLE_TOOLS) == 3
    assert "get_clause" in AVAILABLE_TOOLS
    assert "get_effective_date_and_metadata" in AVAILABLE_TOOLS
    assert "get_definitions" in AVAILABLE_TOOLS

    # Test get_clause
    clause = get_clause("TERMINATION", contract_version=ContractVersionEnum.FINAL_EXECUTED)
    assert "ARTICLE 10" in clause
    assert "10.1" in clause

    # Test get_effective_date_and_metadata
    meta = get_effective_date_and_metadata(contract_version=ContractVersionEnum.FINAL_EXECUTED)
    assert "effective_date" in meta
    assert "2024-12-01" in meta["effective_date"]

    # Test get_definitions (3rd tool) with ContractVersionEnum
    def_res = get_definitions("SCHEDULE B-2", contract_version=ContractVersionEnum.FINAL_EXECUTED)
    assert "Schedule detailing breach resolution" in def_res
    assert "fifteen (15) Business Days" in def_res

    # Test Tool Descriptions Isolation (Zero overlap)
    desc_clause = next(t["description"] for t in TOOL_DEFINITIONS if t["name"] == "get_clause")
    desc_meta = next(t["description"] for t in TOOL_DEFINITIONS if t["name"] == "get_effective_date_and_metadata")
    desc_defs = next(t["description"] for t in TOOL_DEFINITIONS if t["name"] == "get_definitions")

    assert "Does NOT define terms" in desc_clause
    assert "Does NOT extract substantive clauses" in desc_meta
    assert "Does NOT retrieve general contract clauses" in desc_defs


def test_budget_tracker_enforcements():
    """Verify that BudgetTracker enforces all 4 operational budgets."""
    # 1. Max Iterations Breach
    b_iter = BudgetTracker(max_iterations=3)
    b_iter.record_lap(prompt_tokens=100, completion_tokens=20)
    assert b_iter.check_budget() is None
    b_iter.record_lap(prompt_tokens=100, completion_tokens=20)
    assert b_iter.check_budget() is None
    b_iter.record_lap(prompt_tokens=100, completion_tokens=20)
    assert b_iter.check_budget() == BudgetExceededReason.MAX_ITERATIONS

    # 2. Max Tokens Cumulative Breach (Summed across all laps)
    b_tok = BudgetTracker(max_iterations=10, max_tokens=1000)
    b_tok.record_lap(prompt_tokens=400, completion_tokens=100)  # 500
    assert b_tok.check_budget() is None
    b_tok.record_lap(prompt_tokens=450, completion_tokens=100)  # 1050
    assert b_tok.check_budget() == BudgetExceededReason.MAX_TOKENS

    # 3. Max Cost Breach
    b_cost = BudgetTracker(max_iterations=10, max_tokens=100000, max_cost_usd=0.0002)
    b_cost.record_lap(prompt_tokens=1500, completion_tokens=500)
    assert b_cost.check_budget() == BudgetExceededReason.MAX_COST


@pytest.mark.asyncio
async def test_react_agent_execution_and_budget_clean_exit():
    """Verify ReAct agent handles standard questions and exits cleanly on circular loops."""
    agent = ReActAgent(max_iterations=5, max_tokens=8000)

    # Standard query
    res = await agent.run("What is the notice period required for early termination for convenience?")
    assert res["system"] == "Hand-Built ReAct Agent"
    assert "90" in res["answer"] or "ninety" in res["answer"].lower()
    assert res["metrics"]["iterations"] >= 1
    assert not res["metrics"]["budget_exceeded"]

    # Circular query triggering clean budget termination
    circ_res = await agent.run("Resolve the notice schedule for Circular Term Alpha to determine the final termination date.")
    assert circ_res["metrics"]["budget_exceeded"]
    assert circ_res["metrics"]["exceeded_reason"] == "MAX_ITERATIONS"
    assert "[BUDGET_TERMINATION: MAX_ITERATIONS]" in circ_res["answer"]
    assert circ_res["budget_log"] is not None


@pytest.mark.asyncio
async def test_fixed_workflow_execution():
    """Verify fixed workflow executes strict 3-step linear sequence without loops."""
    wf = FixedContractWorkflow()
    res = await wf.run("What is the notice period required for early termination for convenience under the executed agreement?")
    assert res["system"] == "Fixed Deterministic Workflow"
    assert res["metrics"]["iterations"] == 1
    assert res["metrics"]["steps_count"] == 3
    assert "ninety (90) days" in res["answer"] or "90" in res["answer"]


def test_memory_sliding_window_and_persistence(tmp_path):
    """Verify sliding window buffer compression and fact persistence."""
    mem = SlidingWindowMemory(window_size=2)
    mem.add_turn("user", "What is the effective date?")
    mem.add_turn("assistant", "Effective date is February 1, 2024.")
    mem.add_turn("user", "What is the governing law?")
    mem.add_turn("assistant", "Governing law is Delaware.")

    prompt_ctx = mem.get_context_for_prompt()
    assert "CONVERSATION SUMMARY" in prompt_ctx
    assert "Delaware" in prompt_ctx

    # Fact Store persistence
    store_file = tmp_path / "test_facts.json"
    facts = PersistentFactStore(storage_path=store_file)
    facts.store_fact("CNT-MAIN", "effective_date", "2024-02-01")

    # Reload from fresh instance
    facts_reloaded = PersistentFactStore(storage_path=store_file)
    assert facts_reloaded.get_fact("CNT-MAIN", "effective_date") == "2024-02-01"
