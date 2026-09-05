"""
Live End-to-End Test Suite for Week 7 ReAct Agent & Benchmarking API.
Runs against the live running backend API (http://localhost:8080/api/v1/agent).
"""

import os
import sys
import json
import time
import httpx

PORT = os.environ.get("BACKEND_PORT", "8000" if os.path.exists("/.dockerenv") or os.environ.get("PYTHONPATH") == "/app" else "8080")
BASE_URL = os.environ.get("AGENT_API_URL", f"http://localhost:{PORT}/api/v1/agent")


def print_header(title: str):
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)

def test_get_tools():
    print_header("1. Testing GET /api/v1/agent/tools")
    with httpx.Client() as client:
        res = client.get(f"{BASE_URL}/tools")
        print(f"Status Code: {res.status_code}")
        assert res.status_code == 200, f"Expected 200, got {res.status_code}"
        tools = res.json()
        print(f"Retrieved {len(tools)} tools:")
        for t in tools:
            print(f"  - [{t['name']}]: {t['description'][:75]}...")
        assert len(tools) == 3, "Expected exactly 3 typed tools"
        print(">>> Tools Endpoint: PASS")

def test_get_dataset():
    print_header("2. Testing GET /api/v1/agent/race-dataset")
    with httpx.Client() as client:
        res = client.get(f"{BASE_URL}/race-dataset")
        print(f"Status Code: {res.status_code}")
        assert res.status_code == 200, f"Expected 200, got {res.status_code}"
        dataset = res.json()
        print(f"Retrieved {len(dataset)} benchmark race cases:")
        for item in dataset:
            print(f"  - [{item['id']}] ({item['category']}): {item['question'][:60]}...")
        assert len(dataset) == 10, "Expected 10 race dataset items"
        print(">>> Dataset Endpoint: PASS")

def test_query_direct_lookup():
    print_header("3. Testing POST /api/v1/agent/query (Direct Lookup - Convenience Notice)")
    payload = {
        "question": "What is the notice period required for early termination for convenience under the executed agreement?",
        "mode": "both"
    }
    with httpx.Client() as client:
        res = client.post(f"{BASE_URL}/query", json=payload, timeout=30.0)
        print(f"Status Code: {res.status_code}")
        assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
        data = res.json()
        
        react_res = data["react_result"]
        wf_res = data["workflow_result"]
        comp = data["comparison"]
        
        print("\n--- ReAct Agent Result ---")
        print(f"Answer: {react_res['answer']}")
        print(f"Laps: {react_res['budget']['iterations']} | Tokens: {react_res['tokens_used']} | Cost: ${react_res['cost_usd']:.6f} | Latency: {react_res['latency_ms']}ms")
        print("Trace steps:")
        for s in react_res["trace_log"]:
            print(f"  [Lap {s['lap']}] Thought: {s['thought'][:60]}...")
            if s['action_tool']:
                print(f"          Action: {s['action_tool']}({s['action_args']})")
                print(f"          Observation: {str(s['observation'])[:60]}...")
        
        print("\n--- Fixed Workflow Result ---")
        print(f"Answer: {wf_res['answer']}")
        print(f"Tokens: {wf_res['tokens_used']} | Cost: ${wf_res['cost_usd']:.6f} | Latency: {wf_res['latency_ms']}ms")
        
        print("\n--- Side-by-Side Comparison ---")
        print(f"Winner: {comp['winner']} | Reason: {comp['reason']}")
        print(">>> Direct Lookup Query: PASS")

def test_query_multi_hop_dependent():
    print_header("4. Testing POST /api/v1/agent/query (Multi-Hop Defined Term - Cause Notice Deadline)")
    payload = {
        "question": "What is the exact notice deadline for termination for Material Breach under the Final Executed Agreement?",
        "mode": "both"
    }
    with httpx.Client() as client:
        res = client.post(f"{BASE_URL}/query", json=payload, timeout=30.0)
        assert res.status_code == 200
        data = res.json()
        react_res = data["react_result"]
        wf_res = data["workflow_result"]
        
        print(f"ReAct Answer: {react_res['answer']}")
        print(f"Workflow Answer: {wf_res['answer']}")
        print(f"ReAct Steps count: {len(react_res['trace_log'])}")
        
        assert "Schedule B-2" in react_res['answer'] or "15 Business Days" in react_res['answer']
        print(">>> Multi-Hop Query: PASS")

def test_query_circular_budget_stress():
    print_header("5. Testing POST /api/v1/agent/query (Circular Budget Stress Test RACE-010)")
    payload = {
        "question": "Resolve the notice schedule for Circular Term Alpha to determine the final termination date.",
        "mode": "react",
        "max_iterations": 5
    }
    with httpx.Client() as client:
        res = client.post(f"{BASE_URL}/query", json=payload, timeout=30.0)
        assert res.status_code == 200
        data = res.json()
        react_res = data["react_result"]
        budget = react_res["budget"]
        
        print(f"Answer: {react_res['answer']}")
        print(f"Budget breached: {budget['is_breached']} (Reason: {budget['exceeded_reason']})")
        print(f"Total iterations: {budget['iterations']} (Max: {budget['max_iterations']})")
        print(f"Termination log: {react_res['clean_termination_log']}")
        
        assert budget["is_breached"] is True
        assert budget["exceeded_reason"] == "MAX_ITERATIONS"
        print(">>> Circular Budget Stress Test: PASS")

def test_run_full_race():
    print_header("6. Testing POST /api/v1/agent/run-race (Full 10-Question Benchmark)")
    with httpx.Client() as client:
        res = client.post(f"{BASE_URL}/run-race", timeout=60.0)
        assert res.status_code == 200
        data = res.json()
        
        print(f"Total Cases: {data['total_cases']}")
        print(f"Agent Pass Rate: {data['agent_pass_rate_pct']}% | Workflow Pass Rate: {data['workflow_pass_rate_pct']}%")
        print(f"Agent Total Tokens: {data['agent_total_tokens']} | Workflow Total Tokens: {data['workflow_total_tokens']}")
        print(f"Agent Total Cost: ${data['agent_total_cost_usd']:.6f} | Workflow Total Cost: ${data['workflow_total_cost_usd']:.6f}")
        print(f"\nDecision Rule Verdict:\n\"{data['verdict']}\"")
        
        print("\nRace Results Table:")
        print(f"{'ID':<10} | {'Category':<22} | {'Agent Pass':<10} | {'WF Pass':<10} | {'Agent It'}")
        print("-" * 65)
        for r in data["results"]:
            print(f"{r['id']:<10} | {r['category']:<22} | {str(r['agent_passed']):<10} | {str(r['workflow_passed']):<10} | {r['agent_iterations']}")
        
        assert data["agent_pass_rate_pct"] == 100.0
        print(">>> Full Race Benchmark: PASS")

if __name__ == "__main__":
    print_header("STARTING WEEK 7 LIVE API END-TO-END TESTS")
    test_get_tools()
    test_get_dataset()
    test_query_direct_lookup()
    test_query_multi_hop_dependent()
    test_query_circular_budget_stress()
    test_run_full_race()
    print_header("ALL WEEK 7 LIVE API TESTS PASSED SUCCESSFULLY (100%)")
