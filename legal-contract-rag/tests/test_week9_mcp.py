"""
Pytest Suite for Week 9 (Module 5: MCP, Multi-Agent & A2A - Track F: Legal Contracts).
Validates MCP protocol adherence, zero-code extensibility, prompt-engineered docstrings,
recoverable errors, wire tracer annotations, and gateway RBAC scoping.
"""

import os
import pytest
from backend.app.mcp.protocol import (
    JSONRPCRequest,
    JSONRPCResponse,
    InitializeResult,
    ListToolsResult,
    CallToolResult
)
from backend.app.mcp.servers.clause_server import ClauseServer
from backend.app.mcp.servers.repo_server import RepoServer
from backend.app.mcp.config import MCPRegistryConfig, MCPServerConfig, load_mcp_config
from backend.app.mcp.client import MCPClientManager
from backend.app.mcp.gateway import MCPGateway
from backend.app.mcp.wire_tracer import MCPWireTracer
from backend.app.agent.mcp_agent import MCPAgentHost


def test_server1_jsonrpc_handshake_and_discovery():
    """Test ClauseServer initialize and tools/list JSON-RPC 2.0 compliance."""
    server = ClauseServer()

    # 1. Initialize
    init_req = {
        "jsonrpc": "2.0",
        "id": "test-init-1",
        "method": "initialize",
        "params": {"protocolVersion": "2024-11-05"}
    }
    init_res = server.handle_jsonrpc(init_req)
    assert init_res["jsonrpc"] == "2.0"
    assert init_res["id"] == "test-init-1"
    assert "result" in init_res
    assert init_res["result"]["serverInfo"]["name"] == "Contract Clause & Definitions Server"

    # 2. Tools List
    list_req = {
        "jsonrpc": "2.0",
        "id": "test-list-1",
        "method": "tools/list",
        "params": {}
    }
    list_res = server.handle_jsonrpc(list_req)
    assert "result" in list_res
    tools = list_res["result"]["tools"]
    tool_names = [t["name"] for t in tools]
    assert len(tools) == 2
    assert "get_clause" in tool_names
    assert "get_definitions" in tool_names


def test_server2_jsonrpc_handshake_and_discovery():
    """Test RepoServer initialize and tools/list JSON-RPC 2.0 compliance."""
    server = RepoServer()

    init_req = {"jsonrpc": "2.0", "id": "test-init-2", "method": "initialize", "params": {}}
    init_res = server.handle_jsonrpc(init_req)
    assert init_res["result"]["serverInfo"]["name"] == "Contract Repository & Metadata Server"

    list_req = {"jsonrpc": "2.0", "id": "test-list-2", "method": "tools/list", "params": {}}
    list_res = server.handle_jsonrpc(list_req)
    tools = list_res["result"]["tools"]
    tool_names = [t["name"] for t in tools]
    assert len(tools) == 2
    assert "get_contract_metadata" in tool_names
    assert "get_amendment_chain" in tool_names


def test_zero_code_agent_tool_count_expansion():
    """
    Test tool discovery expansion:
    - Server 1 only: 2 tools
    - Server 1 + Server 2: 4 tools
    - MCPAgentHost dynamically recognizes all tools with ZERO code changes.
    """
    tracer = MCPWireTracer()

    # Config 1: Server 1 only
    cfg_s1 = MCPRegistryConfig(
        servers=[
            MCPServerConfig(
                id="clause_server",
                name="Contract Clause & Definitions Server",
                module="backend.app.mcp.servers.clause_server"
            )
        ]
    )
    client_s1 = MCPClientManager(config=cfg_s1, tracer=tracer)
    agent_s1 = MCPAgentHost(client_manager=client_s1)

    assert len(client_s1.list_tools()) == 2
    assert client_s1.get_tool_names() == ["get_clause", "get_definitions"]
    assert len(agent_s1.discovered_tools) == 2
    assert "get_clause" in agent_s1.get_system_prompt()
    assert "get_contract_metadata" not in agent_s1.get_system_prompt()

    # Config 2: Server 1 + Server 2 (Added via config only)
    cfg_all = MCPRegistryConfig(
        servers=[
            MCPServerConfig(
                id="clause_server",
                name="Contract Clause & Definitions Server",
                module="backend.app.mcp.servers.clause_server"
            ),
            MCPServerConfig(
                id="repo_server",
                name="Contract Repository & Metadata Server",
                module="backend.app.mcp.servers.repo_server"
            )
        ]
    )
    client_all = MCPClientManager(config=cfg_all, tracer=tracer)
    agent_all = MCPAgentHost(client_manager=client_all)

    assert len(client_all.list_tools()) == 4
    assert set(client_all.get_tool_names()) == {
        "get_clause", "get_definitions", "get_contract_metadata", "get_amendment_chain"
    }
    assert len(agent_all.discovered_tools) == 4
    assert "get_contract_metadata" in agent_all.get_system_prompt()
    assert "get_amendment_chain" in agent_all.get_system_prompt()


def test_recoverable_error_and_agent_self_correction():
    """
    Test docstring-as-prompt and recoverable error behavior:
    1. Querying Clause 12.4 in CNT-MAIN-2024 returns relocation guidance to Amendment 1.
    2. Agent Host consumes guidance and retrieves active Section 3.1 in CNT-AMD-2024-01.
    """
    tracer = MCPWireTracer()
    client = MCPClientManager(tracer=tracer)
    agent = MCPAgentHost(client_manager=client)

    # 1. Direct tool call check
    raw_res = client.call_tool("get_clause", {"contract_id": "CNT-MAIN-2024", "clause_number": "12.4"})
    assert raw_res.get("isError") is True
    err_text = raw_res["content"][0]["text"]
    assert "relocated to Amendment 1 (CNT-AMD-2024-01)" in err_text

    # 2. Agent autonomous reasoning & self-correction
    result = agent.run_query("Find dispute resolution procedures under Clause 12.4 of CNT-MAIN-2024")
    assert result["contract_id"] == "CNT-MAIN-2024"
    assert "get_clause" in result["tools_invoked"]
    assert "Wilmington, Delaware" in result["final_answer"]
    assert "AAA" in result["final_answer"]
    assert any(step.get("phase") == "Self-Correction & Error Recovery" for step in result["reasoning_steps"])


def test_wire_tracer_packets_and_model_boundary():
    """Test that wire tracer logs packets and contains explicit model boundary notes."""
    tracer = MCPWireTracer()
    client = MCPClientManager(tracer=tracer)

    # Execute a tool call
    client.call_tool("get_clause", {"contract_id": "CNT-MAIN-2024", "clause_number": "8.1"})

    trace = tracer.export_annotated_trace()
    assert trace["title"] == "Annotated Raw JSON-RPC 2.0 MCP Wire Trace"
    assert "EXCLUSIVELY on the Agent Host side" in trace["architecture_boundary_statement"]
    assert trace["trace_summary"]["total_packets"] >= 5

    # Check presence of all message types
    msg_types = [p["message_type"] for p in trace["packets"]]
    assert "initialize_request" in msg_types
    assert "initialize_response" in msg_types
    assert "tools_list_request" in msg_types
    assert "tools_list_response" in msg_types
    assert "tools_call_request" in msg_types
    assert "tools_call_response" in msg_types


def test_gateway_rbac_and_unified_audit_logging():
    """
    Test MCP Gateway:
    - legal_counsel permitted for get_clause & get_contract_metadata
    - external_auditor allowed for metadata, blocked for get_clause
    - Audit log records caller, role, tool, contract_id, status (SUCCESS/BLOCKED)
    """
    client = MCPClientManager()
    gw = MCPGateway(client_manager=client)
    gw.clear_audit_logs()

    # 1. Authorized call (legal_counsel -> get_clause)
    res_counsel = gw.execute_tool(
        tool_name="get_clause",
        arguments={"contract_id": "CNT-MAIN-2024", "clause_number": "8.1"},
        token="token_counsel_002"
    )
    assert res_counsel["gateway_status"] == "SUCCESS"
    assert res_counsel["isError"] is False

    # 2. Blocked call (external_auditor -> get_clause)
    res_auditor = gw.execute_tool(
        tool_name="get_clause",
        arguments={"contract_id": "CNT-MAIN-2024", "clause_number": "8.1"},
        token="token_auditor_004"
    )
    assert res_auditor["gateway_status"] == "BLOCKED"
    assert res_auditor["isError"] is True
    assert "RBAC Access Denied" in res_auditor["content"][0]["text"]

    # 3. Permitted call for auditor (external_auditor -> get_contract_metadata)
    res_auditor_meta = gw.execute_tool(
        tool_name="get_contract_metadata",
        arguments={"contract_id": "CNT-MAIN-2024"},
        token="token_auditor_004"
    )
    assert res_auditor_meta["gateway_status"] == "SUCCESS"
    assert res_auditor_meta["isError"] is False

    # 4. Check unified audit logs
    logs = gw.get_audit_logs()
    assert len(logs) == 3
    statuses = [l["status"] for l in logs]
    assert "BLOCKED" in statuses
    assert "SUCCESS" in statuses
    assert all("duration_ms" in l for l in logs)
    assert all("caller" in l for l in logs)


def test_risk_note_exactly_five_lines():
    """Validate resource/risk_note.md exists and contains exactly 5 non-empty lines."""
    risk_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "resource", "risk_note.md")
    assert os.path.exists(risk_path), "risk_note.md must exist in resource/"

    with open(risk_path, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]

    assert len(lines) == 5, f"Expected exactly 5 lines in risk_note.md, found {len(lines)}"
    assert lines[0].startswith("Author:")
    assert lines[1].startswith("Data Reach:")
    assert lines[2].startswith("Logging:")
    assert lines[3].startswith("Stolen Token Blast Radius:")
    assert lines[4].startswith("Ship Verdict:")
