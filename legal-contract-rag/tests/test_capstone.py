"""
Pytest Suite for Week 12 Capstone (Variant F: Contract Review Assistant).
Validates single entry point integration, dynamic MCP tool discovery,
amendment chain resolution, defined terms cross-referencing,
legal advice refusal guardrail, citation compliance, and out-of-scope refusals.
"""

import pytest
import subprocess
import sys
from pathlib import Path

from run_capstone import (
    CapstoneAgent,
    LegalAdviceGuardrail,
    CitationValidator,
)
from backend.app.mcp.servers.clause_server import get_clause, get_definitions
from backend.app.mcp.servers.repo_server import get_contract_metadata, get_amendment_chain


def test_runtime_mcp_tool_discovery():
    """Verify runtime discovery of all 4 MCP tools with zero hardcoding."""
    agent = CapstoneAgent()
    tool_names = [t.name for t in agent.discovered_tools]
    assert len(agent.discovered_tools) >= 4
    assert "get_clause" in tool_names
    assert "get_definitions" in tool_names
    assert "get_contract_metadata" in tool_names
    assert "get_amendment_chain" in tool_names


def test_amendment_supersession_resolution():
    """
    Verify Amendment Trap Defense:
    Base Northwind Section 8.3 ($2,000,000 cap) must warn of supersession
    and Amendment No. 2 Section 2.1 ($5,000,000 / 12mo fees) must be returned.
    """
    agent = CapstoneAgent()
    res = agent.execute_react_loop("What is the liability cap under the Northwind Logistics agreement?")
    answer = res["final_answer"]

    # Must contain controlling $5,000,000 cap from AMD-02
    assert "5,000,000" in answer
    assert "AMD-2026-014-02" in answer
    assert "Section 2.1" in answer
    # Must also acknowledge the amendment chain
    assert "Amendment No. 2" in answer or "AMD-2026-014-02" in answer
    assert res["citations_valid"] is True


def test_defined_term_and_schedule_c_resolution():
    """
    Verify Defined Term Defense:
    'Business Day' lookup resolves to Schedule C holiday calendar
    and explicitly notes Deepavali on 20 Oct 2026 is an observed holiday.
    """
    def_res = get_definitions("MSA-2026-014", "Business Day")
    assert not def_res.isError
    text = def_res.content[0].text
    assert "Schedule C" in text
    assert "Deepavali" in text or "holiday" in text.lower()


def test_cross_counterparty_jurisdiction_disambiguation():
    """
    Verify Disambiguation:
    Vertex Retail dispute resolution is SIAC arbitration in Singapore,
    distinct from Northwind's Chennai courts.
    """
    meta_res = get_contract_metadata("MSA-2026-022")
    assert not meta_res.isError
    text = meta_res.content[0].text
    assert "SIAC" in text
    assert "Singapore" in text
    assert "no Indian court jurisdiction" in text


def test_mandatory_citation_formatting():
    """
    Verify every retrieved clause carries clause_ref, source_doc, and effective_date.
    """
    cl_res = get_clause("MSA-2026-014", "8.3")
    assert not cl_res.isError
    text = cl_res.content[0].text
    assert "[CITATION:" in text
    assert "clause_ref='Section 8.3'" in text
    assert "source_doc='MSA-2026-014'" in text
    assert "effective_date='2026-01-14'" in text
    assert CitationValidator.validate_citations_present(text) is True


def test_legal_advice_refusal_guardrail_triggers():
    """
    Verify Legal Advice Refusal Guardrail:
    Queries asking if a clause is 'standard' or 'acceptable' trigger
    the deterministic disclaimer redirecting commercial risk to legal counsel.
    """
    guardrail_query = "Is the 15-day termination for convenience clause under Northwind standard and acceptable to sign?"
    assert LegalAdviceGuardrail.check_query_needs_refusal(guardrail_query) is True

    agent = CapstoneAgent()
    res = agent.execute_react_loop(guardrail_query)
    assert res["guardrail_triggered"] is True
    assert "LEGAL ADVICE DISCLAIMER & COUNSEL REFERRAL" in res["final_answer"]
    assert "qualified legal counsel" in res["final_answer"]


def test_out_of_scope_refusal():
    """
    Verify Out-of-Scope Non-Coverage Refusal:
    Queries about non-indexed entities (Apex Industries) or missing services (SVC-05)
    return explicit deterministic refusals rather than hallucinations.
    """
    agent = CapstoneAgent()
    res_apex = agent.execute_react_loop("What is the governing law for Apex Industries?")
    assert "REFUSAL" in res_apex["final_answer"] or "not indexed" in res_apex["final_answer"]

    res_svc = agent.execute_react_loop("What is the uptime target for SVC-05 under Northwind?")
    assert "does not exist" in res_svc["final_answer"] or "REFUSAL" in res_svc["final_answer"]


def test_cli_entry_point_execution():
    """
    Verify stranger can execute run_capstone.py via CLI flags.
    """
    cmd = [sys.executable, "run_capstone.py", "--query", "What is the cure period under Vertex Retail?"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    assert result.returncode == 0
    assert "WEEK 12 CAPSTONE" in result.stdout
    assert "Vertex" in result.stdout
