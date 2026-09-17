"""
Live HTTP Verification Script for Week 9 MCP API Endpoints.
Tests against FastAPI running on http://localhost:8080 or specified base URL.
"""

import sys
import json
import urllib.request
import urllib.error

BASE_URL = "http://localhost:8080/api/v1/mcp"


def make_request(endpoint: str, method: str = "GET", data: dict = None):
    url = f"{BASE_URL}/{endpoint}" if not endpoint.startswith("http") else endpoint
    headers = {"Content-Type": "application/json"}
    body = json.dumps(data).encode("utf-8") if data else None

    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            status_code = resp.getcode()
            res_body = json.loads(resp.read().decode("utf-8"))
            return status_code, res_body
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8")
        try:
            parsed = json.loads(err_body)
        except Exception:
            parsed = {"raw": err_body}
        return e.code, parsed
    except Exception as e:
        return 500, {"error": str(e)}


def test_live_mcp_api():
    print("=" * 80)
    print("TESTING LIVE WEEK 9 MCP FASTAPI ENDPOINTS (http://localhost:8080)")
    print("=" * 80)

    # 1. Test Discovery (All servers vs Server 1 only)
    print("\n1. Testing GET /api/v1/mcp/discovery?config_mode=all ...")
    status, res = make_request("discovery?config_mode=all")
    print(f"   Status: {status}")
    print(f"   Total Tools: {res.get('total_tools')}")
    print(f"   Server Count: {res.get('server_count')}")
    assert status == 200 and res.get('total_tools') == 4, f"Discovery failed: {res}"

    print("\n2. Testing GET /api/v1/mcp/discovery?config_mode=server1_only ...")
    status, res_s1 = make_request("discovery?config_mode=server1_only")
    print(f"   Status: {status}")
    print(f"   Total Tools: {res_s1.get('total_tools')}")
    assert status == 200 and res_s1.get('total_tools') == 2, f"Server 1 discovery failed: {res_s1}"

    # 3. Test Agent Query
    print("\n3. Testing POST /api/v1/mcp/query (Recoverable Error Scenario) ...")
    query_payload = {
        "query": "Find dispute resolution procedures under Clause 12.4 of CNT-MAIN-2024",
        "contract_id": "CNT-MAIN-2024",
        "server_config": "all"
    }
    status, res_q = make_request("query", method="POST", data=query_payload)
    print(f"   Status: {status}")
    print(f"   Tools Discovered: {res_q.get('tools_discovered')}")
    print(f"   Tools Invoked: {res_q.get('tools_invoked')}")
    print(f"   Reasoning Steps: {len(res_q.get('reasoning_steps', []))}")
    print(f"   Final Answer Snippet: {res_q.get('final_answer', '')[:100]}...")
    assert status == 200 and "Wilmington" in res_q.get('final_answer', ''), f"Agent query failed: {res_q}"

    # 4. Test Gateway Execution & RBAC
    print("\n4. Testing POST /api/v1/mcp/call-tool (Gateway with RBAC) ...")
    # Allowed
    tool_payload = {
        "tool_name": "get_clause",
        "arguments": {"contract_id": "CNT-MAIN-2024", "clause_number": "8.1"},
        "token": "token_counsel_002"
    }
    status, res_t = make_request("call-tool", method="POST", data=tool_payload)
    print(f"   Status: {status} | Gateway Status: {res_t.get('gateway_status')}")
    assert status == 200 and res_t.get('gateway_status') == "SUCCESS", f"Gateway allowed call failed: {res_t}"

    # Blocked
    tool_blocked_payload = {
        "tool_name": "get_clause",
        "arguments": {"contract_id": "CNT-MAIN-2024", "clause_number": "8.1"},
        "token": "token_auditor_004"
    }
    status, res_tb = make_request("call-tool", method="POST", data=tool_blocked_payload)
    print(f"   Status: {status} | Gateway Status: {res_tb.get('gateway_status')} (Expected BLOCKED)")
    assert status == 200 and res_tb.get('gateway_status') == "BLOCKED", f"Gateway blocked check failed: {res_tb}"

    # 5. Test Wire Trace
    print("\n5. Testing GET /api/v1/mcp/wire-trace ...")
    status, res_wire = make_request("wire-trace")
    print(f"   Status: {status}")
    print(f"   Total Packets: {res_wire.get('trace_summary', {}).get('total_packets')}")
    print(f"   Boundary Statement: {res_wire.get('architecture_boundary_statement')[:80]}...")
    assert status == 200 and res_wire.get('trace_summary', {}).get('total_packets', 0) > 0, f"Wire trace failed: {res_wire}"

    # 6. Test Audit Logs
    print("\n6. Testing GET /api/v1/mcp/audit-logs ...")
    status, res_audit = make_request("audit-logs")
    print(f"   Status: {status} | Log Entries: {len(res_audit)}")
    assert status == 200 and len(res_audit) >= 2, f"Audit logs failed: {res_audit}"

    # 7. Test Error Demo Endpoint
    print("\n7. Testing GET /api/v1/mcp/error-demo ...")
    status, res_demo = make_request("error-demo")
    print(f"   Status: {status}")
    print(f"   Scenario: {res_demo.get('scenario')}")
    print(f"   Recovery Success: {res_demo.get('model_recovery_success')}")
    assert status == 200 and res_demo.get('model_recovery_success') is True, f"Error demo failed: {res_demo}"

    print("\n" + "=" * 80)
    print("ALL LIVE WEEK 9 MCP API TESTS PASSED SUCCESSFULLY!")
    print("=" * 80)


if __name__ == "__main__":
    test_live_mcp_api()
