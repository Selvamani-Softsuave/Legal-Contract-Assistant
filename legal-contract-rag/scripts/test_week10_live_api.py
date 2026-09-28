"""
Live HTTP Verification Script for Week 10 Multi-Agent Race & A2A Endpoints.
Executes live against the Dockerized backend running at http://localhost:8080.
Tests:
1. /health
2. /api/v1/agent/w10-agent-card (GET)
3. /api/v1/agent/w10-inject-failure (POST)
4. /api/v1/agent/w10-race (POST)
5. /api/v1/agent/w10-handoff-logs (GET)
6. /api/v1/agent/tools (GET)
"""

import sys
import json
import time
import urllib.request
import urllib.error

BASE_URL = "http://localhost:8080"


def make_request(path: str, method: str = "GET", data: dict = None):
    url = f"{BASE_URL}{path}"
    headers = {"Content-Type": "application/json"}
    body = json.dumps(data).encode("utf-8") if data else None

    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    t0 = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            elapsed_ms = (time.perf_counter() - t0) * 1000.0
            status_code = resp.getcode()
            res_body = json.loads(resp.read().decode("utf-8"))
            return status_code, res_body, elapsed_ms
    except urllib.error.HTTPError as e:
        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        err_body = e.read().decode("utf-8")
        try:
            parsed = json.loads(err_body)
        except Exception:
            parsed = {"raw": err_body}
        return e.code, parsed, elapsed_ms
    except Exception as e:
        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        return 500, {"error": str(e)}, elapsed_ms


def run_live_tests():
    print("=" * 80)
    print("LIVE BACKEND SERVER VERIFICATION — WEEK 10 MULTI-AGENT & A2A")
    print(f"Target Server: {BASE_URL}")
    print("=" * 80)

    # 1. Health Check
    print("\n[TEST 1] GET /health ...")
    status, health, el = make_request("/health")
    print(f"  Status: {status} ({el:.1f}ms)")
    print(f"  Service Status: {health.get('status')}")
    print(f"  Version: {health.get('version')}")
    print(f"  Active LLM: {health.get('active_llm', {}).get('provider')} ({health.get('active_llm', {}).get('model')})")
    assert status == 200, f"Health check failed with {status}: {health}"

    # 2. A2A AgentCard
    print("\n[TEST 2] GET /api/v1/agent/w10-agent-card ...")
    status, card_data, el = make_request("/api/v1/agent/w10-agent-card")
    print(f"  Status: {status} ({el:.1f}ms)")
    card = card_data.get("agent_card", {})
    lifecycle = card_data.get("lifecycle_mapping", {})
    print(f"  Agent Name: {card.get('name')} v{card.get('version')}")
    skills = [s.get("name") for s in card.get("capabilities", {}).get("skills", [])]
    print(f"  Advertised Skills: {skills}")
    print(f"  Lifecycle Transition: {lifecycle.get('a2a_lifecycle_mapping', {}).get('state_transition')}")
    print(f"  Target Pause State: {lifecycle.get('a2a_lifecycle_mapping', {}).get('target_state')}")
    assert status == 200 and len(skills) >= 3, "AgentCard verification failed"

    # 3. Worker 500 Failure Injection
    print("\n[TEST 3] POST /api/v1/agent/w10-inject-failure ...")
    status, fail_res, el = make_request(
        "/api/v1/agent/w10-inject-failure?case_id=RACE-005&question=" +
        urllib.parse.quote("What is the exact notice deadline for termination for Material Breach under the Final Executed Agreement?"),
        method="POST"
    )
    print(f"  Status: {status} ({el:.1f}ms)")
    print(f"  Audited Behavior Mode: {fail_res.get('orchestrator_behavior_mode')}")
    print(f"  Mandatory One-Line Summary: {fail_res.get('one_line_summary')}")
    print(f"  Final Answer Snippet: {fail_res.get('final_answer')[:110]}...")
    assert status == 200, "Failure injection call failed"
    assert fail_res.get("orchestrator_behavior_mode") == "DEGRADE_TO_PARTIAL_ANSWER", "Expected degradation mode"

    # 4. Multi-Agent Race Benchmark (Both Arms on 10 Cases)
    print("\n[TEST 4] POST /api/v1/agent/w10-race (Racing Single Agent vs Multi-Agent Squad) ...")
    status, race_res, el = make_request("/api/v1/agent/w10-race", method="POST")
    print(f"  Status: {status} ({el:.1f}ms)")
    print(f"  Total Cases Evaluated: {race_res.get('total_cases')}")

    s_arm = race_res.get("single_agent", {})
    m_arm = race_res.get("multi_agent", {})

    print("\n  --- ARMS HEAD-TO-HEAD COMPARISON ---")
    print(f"  Single Agent Pass Rate : {s_arm.get('pass_rate_pct')}%")
    print(f"  Multi-Agent Pass Rate  : {m_arm.get('pass_rate_pct')}%")
    print(f"  Single Agent p50       : {s_arm.get('p50_latency_seconds'):.4f}s")
    print(f"  Multi-Agent p50        : {m_arm.get('p50_latency_seconds'):.4f}s")
    print(f"  Single Agent p99       : {s_arm.get('p99_latency_seconds'):.4f}s")
    print(f"  Multi-Agent p99        : {m_arm.get('p99_latency_seconds'):.4f}s")
    print(f"  Single Agent Tokens    : {s_arm.get('total_tokens'):,}")
    print(f"  Multi-Agent Tokens     : {m_arm.get('total_tokens'):,}")
    print(f"  Single Agent Cost/Q    : ${s_arm.get('cost_per_question_usd'):.6f}")
    print(f"  Multi-Agent Cost/Q     : ${m_arm.get('cost_per_question_usd'):.6f}")

    print("\n  --- CONTEXT TAX & VERDICT ---")
    print(f"  Multiplier Line : {race_res.get('multiplier_line')}")
    print(f"  Dominant Sink   : {race_res.get('dominant_handoff')} ({race_res.get('dominant_percentage')}%)")
    print(f"  Verdict First 2 Lines:\n    {race_res.get('verdict', '').splitlines()[0]}\n    {race_res.get('verdict', '').splitlines()[1]}")

    assert status == 200, "Race benchmark endpoint failed"
    assert s_arm.get("pass_rate_pct") == 100.0, "Single agent did not achieve 100% pass"
    assert m_arm.get("pass_rate_pct") == 100.0, "Multi agent did not achieve 100% pass"
    assert race_res.get("multiplier") >= 1.0, "Multiplier calculation failed"

    # 5. Handoff Logs Stream
    print("\n[TEST 5] GET /api/v1/agent/w10-handoff-logs ...")
    status, h_logs, el = make_request("/api/v1/agent/w10-handoff-logs")
    print(f"  Status: {status} ({el:.1f}ms)")
    print(f"  Total Hops Logged: {h_logs.get('total_hops')}")
    print(f"  Total Multi Tokens: {h_logs.get('total_multi_tokens'):,}")
    records = h_logs.get("records", [])
    if records:
        print(f"  First Hop: {records[0].get('handoff_name')} ({records[0].get('prompt_tokens')} prompt toks)")
        print(f"  Last Hop : {records[-1].get('handoff_name')} ({records[-1].get('total_tokens')} total toks)")
    assert status == 200, "Handoff logs endpoint failed"

    # 6. Primary Production Single Agent Query Path
    print("\n[TEST 6] POST /api/v1/agent/query (Production Single Agent Execution) ...")
    query_payload = {
        "question": "What is the governing law for the executed agreement?",
        "mode": "react",
        "contract_id": "CNT-MAIN"
    }
    status, q_res, el = make_request("/api/v1/agent/query", method="POST", data=query_payload)
    print(f"  Status: {status} ({el:.1f}ms)")
    react_res = q_res.get("react_result", {})
    print(f"  Single Agent Answer : {react_res.get('answer')}")
    print(f"  Tokens Consumed     : {react_res.get('tokens_used')}")
    print(f"  Cost (USD)          : ${react_res.get('cost_usd'):.6f}")
    print(f"  Trace Steps Laps    : {len(react_res.get('trace_log', []))}")
    assert status == 200, "Production single agent query failed"
    assert "Delaware" in react_res.get("answer", ""), "Answer did not identify Delaware law"

    print("\n" + "=" * 80)
    print("ALL LIVE BACKEND SERVER ENDPOINTS PASSED WITH 100% VERIFICATION SUCCESS!")
    print("=" * 80)


if __name__ == "__main__":
    import urllib.parse
    run_live_tests()

