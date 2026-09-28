"""
Unit and Integration Tests for Week 10 Multi-Agent Race & A2A (Track F - Legal Contracts).
Validates:
1. ClauseRetrievalWorker & DefinedTermsWorker execution and error simulation.
2. HandoffTracker and Context Re-send Multiplier calculation.
3. LegalOrchestrator task decomposition and context re-send tracking.
4. WorkerFailureInjector: 500 injection, behavior classification, and failure_case.md output.
5. A2AAgentCardManager: AgentCard advertisement and task lifecycle mapping.
6. Week10RaceRunner: 4 metrics across both arms, race_table.md, and verdict.md.
7. FastAPI HTTP Endpoints for Week 10.
"""

import os
import pytest
import asyncio
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.agent.multi_agent.workers import ClauseRetrievalWorker, DefinedTermsWorker
from backend.app.agent.multi_agent.handoff_tracker import HandoffTracker
from backend.app.agent.multi_agent.orchestrator import LegalOrchestrator
from backend.app.agent.multi_agent.failure_injector import WorkerFailureInjector
from backend.app.agent.multi_agent.agent_card import A2AAgentCardManager
from backend.app.agent.multi_agent.race_runner import Week10RaceRunner

client = TestClient(app)


@pytest.mark.asyncio
async def test_clause_retrieval_worker():
    worker = ClauseRetrievalWorker()
    res = await worker.execute(contract_id="CNT-MAIN", clause_type="TERMINATION", version="FINAL_EXECUTED")
    assert res["status"] == "SUCCESS"
    assert "ARTICLE 10" in res["clause_text"]
    assert res["prompt_tokens"] > 0
    assert res["completion_tokens"] > 0
    assert res["total_tokens"] == res["prompt_tokens"] + res["completion_tokens"]


@pytest.mark.asyncio
async def test_defined_terms_worker_normal():
    worker = DefinedTermsWorker(inject_failure_500=False)
    res = await worker.execute(contract_id="CNT-MAIN", term="CURE PERIOD", version="FINAL_EXECUTED")
    assert res["status"] == "SUCCESS"
    assert "Thirty (30) calendar days" in res["definition"]
    assert res["total_tokens"] > 0


@pytest.mark.asyncio
async def test_defined_terms_worker_500_failure():
    worker = DefinedTermsWorker(inject_failure_500=True)
    res = await worker.execute(contract_id="CNT-MAIN", term="CURE PERIOD", version="FINAL_EXECUTED")
    assert res["status"] == "HTTP_500_INTERNAL_SERVER_ERROR"
    assert res["definition"] is None
    assert "HTTP 500" in res["error"]


def test_handoff_tracker():
    tracker = HandoffTracker()
    tracker.clear()
    tracker.record_handoff(
        case_id="TEST-001",
        hop_number=1,
        handoff_name="Orchestrator Decomposition",
        from_entity="User",
        to_entity="Orchestrator",
        prompt_tokens=500,
        completion_tokens=50
    )
    tracker.record_handoff(
        case_id="TEST-001",
        hop_number=2,
        handoff_name="Orchestrator -> Clause Worker resend",
        from_entity="Orchestrator",
        to_entity="ClauseWorker",
        prompt_tokens=1000,
        completion_tokens=100,
        is_resend=True
    )
    summary = tracker.compute_summary(single_agent_total_tokens=800)
    assert summary["total_multi_tokens"] == 1650
    assert summary["multiplier"] == round(1650 / 800, 1)
    assert summary["dominant_handoff"] == "Orchestrator -> Clause Worker resend"
    assert "Multi/Single Token Multiplier:" in summary["multiplier_line"]


@pytest.mark.asyncio
async def test_legal_orchestrator_execution():
    orchestrator = LegalOrchestrator()
    res = await orchestrator.run(
        question="What is the notice period required for early termination for convenience under the executed agreement?",
        contract_id="CNT-MAIN",
        case_id="RACE-001"
    )
    assert "90" in res["answer"]
    assert "Article 10" in res["article_cited"]
    assert res["tokens_used"] > 0
    assert res["cost_usd"] > 0


@pytest.mark.asyncio
async def test_worker_failure_injection():
    res = await WorkerFailureInjector.run_failure_simulation()
    assert res["case_id"] == "RACE-005"
    assert res["orchestrator_behavior_mode"] == "DEGRADE_TO_PARTIAL_ANSWER"
    assert "degraded to a partial answer" in res["one_line_summary"]
    assert "DEGRADED PARTIAL ANSWER" in res["final_answer"]

    # Verify failure_case.md file was created
    failure_md = os.path.join(os.path.dirname(os.path.dirname(__file__)), "resource", "failure_case.md")
    assert os.path.exists(failure_md)


def test_a2a_agent_card():
    data = A2AAgentCardManager.get_agent_card_data()
    card = data["agent_card"]
    lifecycle = data["lifecycle_mapping"]

    assert card["name"] == "LegalContractOrchestrator"
    assert len(card["capabilities"]["skills"]) >= 3
    assert "BearerToken" in card["authentication"]["type"]
    assert lifecycle["a2a_lifecycle_mapping"]["target_state"] == "input-required"
    assert len(lifecycle["a2a_vs_rest_two_line_verdict"]) > 20


@pytest.mark.asyncio
async def test_w10_race_runner():
    res = await Week10RaceRunner.run_race()
    assert res["total_cases"] == 10
    assert res["single_agent"]["pass_rate_pct"] == 100.0
    assert res["multi_agent"]["pass_rate_pct"] == 100.0
    assert res["multiplier"] > 1.0
    assert "KEEP Single Agent, KILL Multi-Agent Squad" in res["verdict"]

    # Verify race_table.md and verdict.md exist
    race_table = os.path.join(os.path.dirname(os.path.dirname(__file__)), "resource", "race_table.md")
    verdict_md = os.path.join(os.path.dirname(os.path.dirname(__file__)), "resource", "verdict.md")
    assert os.path.exists(race_table)
    assert os.path.exists(verdict_md)


def test_fastapi_w10_endpoints():
    # 1. Handoff logs
    h_res = client.get("/api/v1/agent/w10-handoff-logs")
    assert h_res.status_code == 200
    h_data = h_res.json()
    assert "total_hops" in h_data
    assert "multiplier" in h_data

    # 2. Agent Card
    a_res = client.get("/api/v1/agent/w10-agent-card")
    assert a_res.status_code == 200
    a_data = a_res.json()
    assert "agent_card" in a_data
    assert "lifecycle_mapping" in a_data

    # 3. Failure injection
    f_res = client.post("/api/v1/agent/w10-inject-failure")
    assert f_res.status_code == 200
    f_data = f_res.json()
    assert f_data["orchestrator_behavior_mode"] == "DEGRADE_TO_PARTIAL_ANSWER"
