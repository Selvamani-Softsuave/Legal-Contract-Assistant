<!-- Soft Suave · The AI Engineering League -->
# Week 10 Practical — Task Set F

## Race the contract squad against your single agent

| | |
|---|---|
| Domain | Legal contracts |
| Week | 10 — Multi-Agent & A2A — With Evidence, Not Fashion |
| Module | M5 — MCP, Multi-agent & A2A |
| Sat on | Week 11 · Monday |
| Marks | 100 |

> **This is an extension of the app you already built in Week 10.** It is not a build from scratch, and it tests only this week's concepts. Bring your numbers written down.


---

## 1. Problem statement

You spent last week building an orchestrator that decomposes a contract question, delegates to a clause-retrieval worker and a defined-terms worker, and synthesises the answer. The partner sponsoring this wants to know whether it beats the single agent you already had, or just costs more per question. Race them today on the same 10 Week-6 eval cases and report the bill alongside the pass rate.


---

## 2. Requirements

1. Run the SAME 10 Week-6 eval cases through both the single agent and the orchestrator, with the same judge. Do not write new cases — a changed eval set voids the comparison.
2. Report all four numbers for BOTH arms in one table: pass rate, p50 and p99 latency, total tokens, cost per question.
3. Compute the context re-send multiplier (multi tokens / single tokens, one decimal place) and attribute the single largest token share to a named hand-off from your log — e.g. "orchestrator -> clause worker resend, 41% of all tokens".
4. Inject one worker failure: make the defined-terms worker return a 500 on one case. Record what the orchestrator actually did — retried, degraded to a partial answer, or lied by interpreting a defined term it never looked up — and say which in one line.
5. Write the verdict: keep or kill, citing at least two of the four numbers, and name the sunk-cost bias out loud before you state it.


---

## 3. Expected output

race_table.md (4 metrics x 2 arms), handoffs.log with per-hand-off token counts, multiplier line with the attributed hand-off, failure_case.md, verdict.md (max 10 lines).


---

## 4. Evaluation rubric

| Criterion | Points |
|---|---|
| All four numbers reported for BOTH arms on the same 10 Week-6 cases: pass rate, p50/p99 latency, total tokens, cost per task | 30 |
| Context re-send multiplier computed and attributed to a specific hand-off from the log | 25 |
| Worker failure injected and the orchestrator's actual behaviour (retry / degrade / lie) recorded honestly | 20 |
| Verdict cites at least two of the four numbers and names the sunk-cost bias out loud | 15 |
| Hand-off log with per-hand-off token counts | 10 |
| **Total** | **100** |

*Zero points for polish, UI, or "it works". This mirrors the House rubric: failure-finding and a number that moved are what score.*


---

## 5. Bonus challenge

Publish the AgentCard your orchestrator would advertise (skills, input/output modes, auth), then map the failed case onto the A2A task lifecycle: state whether that case should have ended failed or paused at input-required to ask which amendment date governs, and say in two lines what A2A buys you over a plain REST call to the worker.


---

## 6. Submission checklist

- [ ] race_table.md — 4 metrics x 2 arms, same 10 cases named
- [ ] handoffs.log — every hand-off with its token count
- [ ] Multiplier line: multi/single tokens to one decimal, with the dominant hand-off named
- [ ] failure_case.md — the injected 500 and what the orchestrator actually did
- [ ] verdict.md — keep/kill, two numbers cited, sunk-cost named


---

## 7. Common mistakes

- **Declaring multi-agent the winner on pass rate while ignoring a 9x token bill — either result clears the gate, but only with all four numbers.**
- **Building a fresh eval set because the Week-6 cases 'do not suit the orchestrator' — you have just changed the ruler mid-measurement and neither number means anything now.**
- **Re-sending the full executed agreement plus every amendment to both workers on each hop, then concluding multi-agent is inherently expensive — you tested your context strategy, not the pattern.**
- **Giving the clause worker every tool the single agent had, which deletes the narrow-prompt-fewer-tools constraint that was the only plausible source of a win.**
- **Passing the clause worker the minimum context and dropping the governing effective date, so it answers off the superseded clause — that is a context bug you then blame on the pattern.**
- **Reporting p50 only because p99 was embarrassing — the client notices the p99, which is exactly the question asked during a live negotiation.**


---

*Set F of 6. Sets A–F are equivalent in difficulty and objectives; only the domain differs.*
