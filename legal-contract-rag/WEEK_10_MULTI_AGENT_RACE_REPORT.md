# Week 10 Comprehensive Practical Report: Multi-Agent & A2A — With Evidence, Not Fashion
## Track F: Legal Contracts — Empirical Race, Context Tax & Final Verdict

---

## Executive Summary

This report documents the rigorous head-to-head race between our **Single Agent** (with direct MCP tool access) and the **Multi-Agent Orchestrator Squad** (Manager + Clause Retrieval Worker + Defined-Terms Worker) evaluated across the identical 10 contract test cases (`RACE-001` through `RACE-010`).

Both arms achieved a **100.0% Pass Rate**, but the Multi-Agent Squad imposed an exorbitant price tag:
- **1.4x Token Multiplier** (25,019 tokens vs 18,091 tokens).
- **~13.4x Cost Penalty** per question.
- **~3.0x p99 Latency Blowout** (0.0021s vs 0.0007s).

The empirical conclusion is undeniable: **Multi-agent architecture is KILLED; Single Agent is KEPT for production.**

---

## Official 4-Metric Race Scorecard

| Evaluation Metric | Single Agent (Production Path) | Multi-Agent Orchestrator Squad | Delta / Multi-Agent Tax | Rubric Target |
|---|:---:|:---:|:---:|:---:|
| **Pass Rate (%)** | **100.0%** | **100.0%** | **0.0%** (Identical Accuracy) | 30 pts |
| **p50 Latency (s)** | **0.0002s** | **0.0016s** | **+0.0015s** | 30 pts |
| **p99 Latency (s)** | **0.0007s** | **0.0021s** | **+0.0014s** | 30 pts |
| **Total Tokens** | **18,091** | **25,019** | **+6,928 tokens** | 30 pts |
| **Cost Per Question** | **$0.000336** | **$0.004503** | **+$0.004167** | 30 pts |

---

## Context Re-send Multiplier & Token Sink Attribution

```text
Multi/Single Token Multiplier: 1.4x (Dominant Hand-off: Orchestrator -> Defined-Terms Worker resend, 38.5% of all tokens)
```

Every handoff hop between agents re-serializes the growing conversation history. The single largest token sink was `Orchestrator -> Defined-Terms Worker resend`, representing **38.5% of the entire token budget**.

---

## Injected Worker Failure (HTTP 500 Simulation)

On test case `RACE-005`, we injected an HTTP 500 failure on the `DefinedTermsWorker`.
* **Orchestrator Reaction**: Degraded to a partial answer. It cited Article 10.2 but transparently disclosed that Schedule B-2 notice period definitions were unavailable.
* **Liability Prevention**: Crucially, the orchestrator refused to synthesize an ungrounded parametric guess, preventing legal malpractice liability.

---

## Final Verdict & Sunk-Cost Declaration

```text
# Verdict: KEEP Single Agent, KILL Multi-Agent Squad
1. Single Agent achieves 100.0% Pass Rate matching the Multi-Agent Squad (100.0%).
2. Multi-Agent imposes a massive 1.4x Token Multiplier (25019 vs 18091 tokens).
3. Cost per question is ~3x higher on Multi-Agent ($0.004503 vs $0.000336).
4. p99 Latency is unacceptable on Multi-Agent (0.0021s vs 0.0007s single agent).
5. Dominant token sink is 'Orchestrator -> Defined-Terms Worker resend' consuming 38.5% of all tokens.
6. SUNK-COST BIAS NAMED: We spent substantial engineering hours decomposing schemas and wiring
   orchestrators and workers, creating an emotional urge to keep multi-agent simply because we built it.
7. The empirical evidence decisively kills multi-agent for legal QA: it is slower, 3x pricier, and yields 0% accuracy gain.
8. DECISION: KILL the Multi-Agent Orchestrator. Standardize 100% on Single Agent with MCP Tools.
```

---

## Bonus Challenge: A2A AgentCard & Task Lifecycle

1. **Advertised AgentCard**: Published in `resource/agent_card.json`, exposing skills `extract_contract_clauses`, `resolve_defined_terms`, and `synthesize_legal_qa` with OAuth2 Bearer authentication.
2. **A2A Task Lifecycle Mapping**: On worker failure, A2A pauses the task at `input-required` (querying counsel for the governing amendment date) rather than terminating in a hard HTTP 500 failure.
3. **A2A vs REST Value Statement**:
   *A2A provides an asynchronous, stateful task lifecycle with native human-in-the-loop pause states (input-required), whereas plain REST is a synchronous, stateless pipe that collapses into unrecoverable 500 dead-ends when sub-agents fail.*
