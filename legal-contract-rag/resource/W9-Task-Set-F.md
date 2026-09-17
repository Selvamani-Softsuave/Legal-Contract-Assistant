<!-- Soft Suave · The AI Engineering League -->
# Week 9 Practical — Task Set F

## Bolt on the contract-repository server without touching the agent

| | |
|---|---|
| Domain | Legal contracts |
| Week | 9 — MCP — the Standard Way Agents Reach Tools & Data |
| Module | M5 — MCP, Multi-agent & A2A |
| Sat on | Week 10 · Monday |
| Marks | 100 |

> **This is an extension of the app you already built in Week 9.** It is not a build from scratch, and it tests only this week's concepts. Bring your numbers written down.


---

## 1. Problem statement

The knowledge team has stood up an MCP server over the contract repository that exposes lookup by contract id, its effective date, and its amendment chain. Legal wants your assistant using it before the renewal review on Thursday, and they are not waiting for a code release. Your Week-9 agent already discovers tools from your own clause-search server — prove that discovery was real by adding server two with nothing but config.


---

## 2. Requirements

1. Add the contract-repository server to your agent's MCP config and run one query that provably calls a tool from it (show the tool name in the trace).
2. Produce a git diff proving ZERO lines changed in your agent module between server one and server one plus two — config changes only.
3. Report the number of tools discovered before and after, with names, from tools/list — not from your own notes.
4. Capture the raw JSON-RPC initialize -> tools/list -> tools/call exchange against the new server, annotate every top-level field by hand, and state in one line where the model call happens and where it does not.
5. Rewrite ONE tool docstring on YOUR OWN server as a prompt and make one of its error paths recoverable (e.g. "no clause 12.4 in MSA-2021-0142 as amended: clauses run 1-11, see Amendment 2 effective 2023-06-01" not "Error 3"), then show a before/after transcript of the model handling that same failing call.
6. Write a 5-line supply-chain risk note for the contract-repository server: who wrote it, what it can reach, what it logs, what a stolen token could do, ship or don't.


---

## 3. Expected output

agent_diff.txt (zero changed lines), the config diff, wire.json with hand annotations, tool counts before -> after with names, error_before_after.md transcript, risk_note.md (5 lines).


---

## 4. Evaluation rubric

| Criterion | Points |
|---|---|
| Config-only server swap proven by diff: agent module shows zero changed lines | 30 |
| Raw initialize/tools-list/tools-call captured and annotated, model-call location stated correctly | 25 |
| Docstring-as-prompt plus recoverable-error rewrite, evidenced by a before/after model transcript | 20 |
| Tool count reported before and after discovery, with names, taken from tools/list | 15 |
| Five-line third-party risk note answering who wrote it, what it reaches, what it logs | 10 |
| **Total** | **100** |

*Zero points for polish, UI, or "it works". This mirrors the House rubric: failure-finding and a number that moved are what score.*


---

## 5. Bonus challenge

Put both servers behind one gateway process: the agent connects to one front door, the gateway fans out, and every tools/call is written to a single audit line with caller, tool, and contract id. Then scope a token so the amendment-chain tool is denied while base contract lookup still works, and show the denial reaching the model as a recoverable message.


---

## 6. Submission checklist

- [ ] agent_diff.txt showing 0 changed lines in the agent module
- [ ] config diff adding the second server
- [ ] wire.json — raw initialize, tools/list, tools/call, annotated
- [ ] Tool count line: N before -> M after, with tool names
- [ ] error_before_after.md — same failing call, old docstring/error vs new
- [ ] risk_note.md — exactly 5 lines


---

## 7. Common mistakes

- **Hard-coding the tool list after connecting to the server, which throws away the entire point of discovery — your diff should show the agent unchanged when you add server two.**
- **Putting an LLM call inside your MCP server so it 'summarises the clause' — the server exposes a capability, the host runs the model, and this mistake means you never understood the architecture.**
- **Exposing the defined-terms schedule as a tool when it is context the app should attach — resources are app-attached, tools are model-invoked, and the wrong choice makes the model call out for definitions it should have been handed with the clause.**
- **Swallowing the wrong-effective-date lookup into 'Error: not found', so the model cannot tell 'that amendment predates the contract' from 'the repository is down' and answers off the unamended original.**
- **Adding the third-party repository server because it worked, without asking what it can reach — it now runs inside your agent's trust boundary with a token that reads every executed contract, including the ones under NDA.**


---

*Set F of 6. Sets A–F are equivalent in difficulty and objectives; only the domain differs.*
