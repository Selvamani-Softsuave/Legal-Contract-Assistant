# Track F: Docstring-as-Prompt & Recoverable Error Design

## 1. Docstring Evolution (Docstring-as-Prompt)

### Before (Standard Code Docstring)
```python
def get_clause(contract_id: str, clause_number: str):
    """Retrieve contract clause by ID and number."""
```
*Why this fails*: The model has zero guidance on when to call this tool versus other tools, how to handle partial queries, or what to do if a clause is moved or amended.

### After (Prompt-Engineered MCP Tool Docstring)
```python
def get_clause(contract_id: str, clause_number: Optional[str] = None, clause_type: Optional[str] = None) -> CallToolResult:
    """
    Retrieve the exact legal text, section number, and title of a specific clause in a contract.
    Use this tool whenever the user asks for obligations, termination conditions, indemnification,
    liability caps, or specific clause provisions. Provide the contract_id (e.g. 'CNT-MAIN-2024')
    and either a clause_type (e.g. 'termination', 'indemnification', 'confidentiality') or clause_number (e.g. '12.4').
    If the clause is missing, this tool returns structural guidance indicating where the provision was relocated or amended.
    """
```
*Why this succeeds*: Teaches the model exact invocation triggers, parameter formats, semantic fallback options, and hints at actionable self-correction paths.

---

## 2. Error Response Comparison

### Before: Generic Unhelpful Error
```json
{
  "isError": true,
  "content": [
    {
      "type": "text",
      "text": "Error 3: Clause not found"
    }
  ]
}
```

### After: Context-Rich Recoverable Error
```json
{
  "isError": true,
  "content": [
    {
      "type": "text",
      "text": "Clause 12.4 was not found in 'CNT-MAIN-2024'. Note: Dispute escalation terms in this contract were relocated to Amendment 1 (CNT-AMD-2024-01), Section 3. Use 'get_amendment_chain' or search 'CNT-AMD-2024-01' for current binding terms."
    }
  ]
}
```

---

## 3. Host Agent Model Transcripts

### Transcript Before (Generic Error -> Failure / Dead End)
```
[USER] What are the dispute escalation procedures in Clause 12.4 of CNT-MAIN-2024?

[HOST AGENT] Thinking: User wants Clause 12.4 from CNT-MAIN-2024.
[ACTION] Dispatching tools/call -> get_clause(contract_id='CNT-MAIN-2024', clause_number='12.4')
[OBSERVATION] Error 3: Clause not found

[HOST AGENT] Final Answer:
I searched for Clause 12.4 in contract CNT-MAIN-2024, but the system returned an error indicating the clause does not exist. Please check the clause number and try again.
```

---

### Transcript After (Recoverable Error -> Autonomous Self-Correction & Success)
```
[USER] What are the dispute escalation procedures in Clause 12.4 of CNT-MAIN-2024?

[HOST AGENT] Thinking: User is querying dispute escalation under Clause 12.4 in CNT-MAIN-2024.
[ACTION 1] Dispatching tools/call -> get_clause(contract_id='CNT-MAIN-2024', clause_number='12.4')
[OBSERVATION 1] Clause 12.4 was not found in 'CNT-MAIN-2024'. Note: Dispute escalation terms in this contract were relocated to Amendment 1 (CNT-AMD-2024-01), Section 3. Use 'get_amendment_chain' or search 'CNT-AMD-2024-01' for current binding terms.

[HOST AGENT] Self-Correction & Recovery:
The tool observation indicates Clause 12.4 was relocated to Amendment 1 (CNT-AMD-2024-01), Section 3.
I will follow the tool's guidance and query the active binding dispute terms from CNT-AMD-2024-01.

[ACTION 2] Dispatching tools/call -> get_clause(contract_id='CNT-AMD-2024-01', clause_number='3.1')
[OBSERVATION 2] [CNT-AMD-2024-01] Clause 3.1 - Mandatory Escalation & Binding Arbitration (Type: dispute_resolution)
Text: "All disputes arising out of or in connection with the Master Services Agreement shall first be submitted to senior executives for 14-day negotiation, and failing resolution, settled by binding arbitration under AAA rules in Wilmington, Delaware."

[HOST AGENT] Final Answer:
In the Master Services Agreement (CNT-MAIN-2024), former Clause 12.4 was superseded and relocated to Amendment 1 (CNT-AMD-2024-01), Section 3.1.

Under the current binding terms:
1. Senior Executive Escalation: Any dispute must first be submitted to senior executives of both parties for a mandatory 14-day good-faith negotiation period.
2. Binding Arbitration: If unresolved after 14 days, disputes are settled through binding arbitration administered by the American Arbitration Association (AAA) in Wilmington, Delaware.
```
