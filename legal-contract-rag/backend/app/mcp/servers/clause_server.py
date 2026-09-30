"""
MCP Server 1: Contract Clause & Definitions Server.
Exposes tools for retrieving contract clauses and legal term definitions.
Features prompt-engineered tool docstrings and recoverable, context-rich error paths.
"""

import json
from typing import Any, Dict, List, Optional

from backend.app.mcp.protocol import (
    JSONRPCRequest,
    JSONRPCResponse,
    JSONRPCError,
    InitializeResult,
    ServerInfo,
    ServerCapabilities,
    ListToolsResult,
    MCPToolDefinition,
    ToolInputSchema,
    CallToolResult,
    ToolContent,
)

SERVER_INFO = ServerInfo(name="Contract Clause & Definitions Server", version="1.1.0")

# In-memory contract knowledge base for MCP demonstrations & test cases
MOCK_CLAUSES = {
    "CNT-MAIN-2024": {
        "title": "Master Services Agreement (Acme Corp & Zeta Tech)",
        "clauses": {
            "1.1": {
                "number": "1.1",
                "type": "definitions",
                "title": "Definitions & Interpretations",
                "text": "Definitions: 'Affiliate' means any entity controlling, controlled by, or under common control. 'Confidential Information' means all non-public proprietary materials. 'Effective Date' means January 15, 2024."
            },
            "4.2": {
                "number": "4.2",
                "type": "confidentiality",
                "title": "Confidentiality Obligations",
                "text": "Recipient shall protect Disclosing Party's Confidential Information with at least reasonable care and shall not disclose such information to any third party without prior written consent for a period of five (5) years."
            },
            "8.1": {
                "number": "8.1",
                "type": "limitation_of_liability",
                "title": "Aggregate Liability Cap",
                "text": "In no event shall either party's total aggregate liability arising out of or related to this Agreement exceed the total fees paid or payable by Customer in the twelve (12) months preceding the incident giving rise to liability."
            },
            "9.3": {
                "number": "9.3",
                "type": "termination",
                "title": "Termination for Cause",
                "text": "Either party may terminate this Agreement immediately upon written notice if the other party materially breaches any provision and fails to cure such breach within thirty (30) days of receiving written notice."
            },
            "11.0": {
                "number": "11.0",
                "type": "indemnification",
                "title": "Mutual Indemnification",
                "text": "Provider agrees to defend, indemnify, and hold harmless Customer against any third-party claims alleging that Customer's authorized use of the Services infringes any patent, copyright, or trademark."
            }
        },
        "definitions": {
            "Confidential Information": "All non-public proprietary materials, code, customer lists, and financial statements designated as confidential or reasonably understood to be confidential.",
            "Material Breach": "A failure of performance under this Agreement that substantially undermines the contract's benefit for the non-breaching party.",
            "Effective Date": "January 15, 2024, the date this Agreement becomes legally binding between the Parties.",
            "Service Credits": "Financial deductions applied against subsequent invoices for failure to meet agreed Service Level Commitments."
        },
        "relocated_clauses": {
            "12.4": {
                "topic": "Dispute Escalation & Mandatory Arbitration",
                "target_contract": "CNT-AMD-2024-01",
                "target_section": "Section 3 (Arbitration Protocol)",
                "note": "Dispute escalation terms in this contract were relocated to Amendment 1 (CNT-AMD-2024-01), Section 3. Use 'get_amendment_chain' or search 'CNT-AMD-2024-01' for current binding terms."
            }
        }
    },
    "CNT-AMD-2024-01": {
        "title": "Amendment 1 to Master Services Agreement",
        "clauses": {
            "3.1": {
                "number": "3.1",
                "type": "dispute_resolution",
                "title": "Mandatory Escalation & Binding Arbitration",
                "text": "All disputes arising out of or in connection with the Master Services Agreement shall first be submitted to senior executives for 14-day negotiation, and failing resolution, settled by binding arbitration under AAA rules in Wilmington, Delaware."
            }
        },
        "definitions": {
            "AAA Rules": "The Commercial Arbitration Rules of the American Arbitration Association then in effect."
        },
        "relocated_clauses": {}
    }
}


def get_clause(contract_id: str, clause_number: Optional[str] = None, clause_type: Optional[str] = None) -> CallToolResult:
    """
    Retrieve the exact legal text, section number, and title of a specific clause in a contract.
    Use this tool whenever the user asks for obligations, termination conditions, indemnification,
    liability caps, or specific clause provisions. Provide the contract_id (e.g. 'CNT-MAIN-2024')
    and either a clause_type (e.g. 'termination', 'indemnification', 'confidentiality') or clause_number (e.g. '12.4').
    If the clause is missing, this tool returns structural guidance indicating where the provision was relocated or amended.
    """
    contract = MOCK_CLAUSES.get(contract_id)
    if not contract:
        error_msg = (
            f"Contract '{contract_id}' was not found in the Clause Repository. "
            f"Available contract IDs in this repository include: {', '.join(MOCK_CLAUSES.keys())}. "
            "Please check the identifier or use 'get_contract_metadata' on the Repository Server."
        )
        return CallToolResult(content=[ToolContent(text=error_msg)], isError=True)

    clauses = contract.get("clauses", {})
    
    # 1. Search by clause_number
    if clause_number:
        if clause_number in clauses:
            c = clauses[clause_number]
            result_text = (
                f"[{contract_id}] Clause {c['number']} - {c['title']} (Type: {c['type']})\n"
                f"Text: \"{c['text']}\""
            )
            return CallToolResult(content=[ToolContent(text=result_text)], isError=False)
        
        # Check relocated clauses (Docstring-as-prompt & Recoverable Error requirement)
        relocated = contract.get("relocated_clauses", {}).get(clause_number)
        if relocated:
            recoverable_msg = (
                f"Clause {clause_number} was not found in '{contract_id}'. "
                f"Note: {relocated['note']}"
            )
            return CallToolResult(content=[ToolContent(text=recoverable_msg)], isError=True)
        else:
            available_nums = list(clauses.keys())
            recoverable_msg = (
                f"Clause {clause_number} was not found in '{contract_id}'. "
                f"Available clauses in this contract are: {', '.join(available_nums)}. "
                "You may query by clause_type (e.g. 'termination', 'indemnification') or check amendments."
            )
            return CallToolResult(content=[ToolContent(text=recoverable_msg)], isError=True)

    # 2. Search by clause_type
    if clause_type:
        normalized_type = clause_type.lower().strip().replace(" ", "_").replace("-", "_")
        matches = [c for c in clauses.values() if normalized_type in c["type"].lower() or normalized_type in c["title"].lower()]
        if matches:
            lines = [f"Found {len(matches)} clause(s) matching type '{clause_type}' in {contract_id}:"]
            for c in matches:
                lines.append(f"\n- Clause {c['number']} ({c['title']}): \"{c['text']}\"")
            return CallToolResult(content=[ToolContent(text="\n".join(lines))], isError=False)
        else:
            avail_types = list(set(c["type"] for c in clauses.values()))
            recoverable_msg = (
                f"No clause of type '{clause_type}' found in '{contract_id}'. "
                f"Available clause types in this document: {', '.join(avail_types)}. "
                "Try searching with one of the available types or query by section number."
            )
            return CallToolResult(content=[ToolContent(text=recoverable_msg)], isError=True)

    # Return overview of clauses if neither specified
    all_clauses = [f"Clause {c['number']}: {c['title']}" for c in clauses.values()]
    return CallToolResult(
        content=[ToolContent(text=f"Contract '{contract_id}' contains clauses:\n" + "\n".join(all_clauses))],
        isError=False
    )


def get_definitions(contract_id: str, term: Optional[str] = None) -> CallToolResult:
    """
    Retrieve defined terms, legal interpretations, and glossary definitions from Section 1 or Appendix A of a contract.
    Use this tool to resolve the precise contractual meaning of capitalized terms (e.g., 'Confidential Information', 'Material Breach', 'Applicable Law').
    Provide the contract_id and an optional term filter.
    """
    contract = MOCK_CLAUSES.get(contract_id)
    if not contract:
        return CallToolResult(
            content=[ToolContent(text=f"Contract '{contract_id}' not found. Available: {', '.join(MOCK_CLAUSES.keys())}")],
            isError=True
        )

    defs = contract.get("definitions", {})
    if term:
        term_clean = term.strip()
        matches = {k: v for k, v in defs.items() if term_clean.lower() in k.lower()}
        if matches:
            output = [f"Definition(s) for '{term}' in {contract_id}:"]
            for k, v in matches.items():
                output.append(f"\n• \"{k}\": {v}")
            return CallToolResult(content=[ToolContent(text="\n".join(output))], isError=False)
        else:
            avail_terms = list(defs.keys())
            return CallToolResult(
                content=[ToolContent(text=f"Term '{term}' not defined in '{contract_id}'. Defined terms available: {', '.join(avail_terms)}.")],
                isError=True
            )

    output = [f"Defined terms in contract '{contract_id}':"]
    for k, v in defs.items():
        output.append(f"• \"{k}\": {v}")
    return CallToolResult(content=[ToolContent(text="\n".join(output))], isError=False)


TOOLS = [
    MCPToolDefinition(
        name="get_clause",
        description=(
            "Retrieve the exact legal text, section number, and title of a specific clause in a contract. "
            "Use this tool whenever the user asks for obligations, termination conditions, indemnification, "
            "liability caps, or specific clause provisions. Provide the contract_id (e.g. 'CNT-MAIN-2024') "
            "and either a clause_type (e.g. 'termination', 'indemnification', 'confidentiality') or clause_number (e.g. '12.4'). "
            "If the clause is missing, this tool returns structural guidance indicating where the provision was relocated or amended."
        ),
        inputSchema=ToolInputSchema(
            type="object",
            properties={
                "contract_id": {
                    "type": "string",
                    "description": "Unique identifier of the contract (e.g. 'CNT-MAIN-2024' or 'CNT-AMD-2024-01')"
                },
                "clause_number": {
                    "type": "string",
                    "description": "Specific clause number to lookup (e.g. '1.1', '4.2', '8.1', '9.3', '12.4')"
                },
                "clause_type": {
                    "type": "string",
                    "description": "Category/type of clause (e.g. 'termination', 'indemnification', 'confidentiality', 'limitation_of_liability')"
                }
            },
            required=["contract_id"]
        )
    ),
    MCPToolDefinition(
        name="get_definitions",
        description=(
            "Retrieve defined terms, legal interpretations, and glossary definitions from Section 1 or Appendix A of a contract. "
            "Use this tool to resolve the precise contractual meaning of capitalized terms (e.g., 'Confidential Information', 'Material Breach', 'Applicable Law'). "
            "Provide the contract_id and an optional term filter."
        ),
        inputSchema=ToolInputSchema(
            type="object",
            properties={
                "contract_id": {
                    "type": "string",
                    "description": "Unique identifier of the contract (e.g. 'CNT-MAIN-2024')"
                },
                "term": {
                    "type": "string",
                    "description": "Optional specific term name to search for (e.g. 'Confidential Information', 'Material Breach')"
                }
            },
            required=["contract_id"]
        )
    )
]


class ClauseServer:
    """In-process and JSON-RPC dispatchable MCP Server for Clauses & Definitions."""

    def __init__(self):
        self.server_info = SERVER_INFO
        self.tools = TOOLS

    def handle_jsonrpc(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process incoming JSON-RPC 2.0 requests according to the MCP specification."""
        try:
            req = JSONRPCRequest(**request_data)
        except Exception as e:
            return JSONRPCResponse(
                id=request_data.get("id"),
                error=JSONRPCError(code=-32700, message=f"Parse error: {str(e)}")
            ).model_dump(exclude_none=True)

        if req.method == "initialize":
            res = InitializeResult(
                protocolVersion="2024-11-05",
                capabilities=ServerCapabilities(tools={"listChanged": False}),
                serverInfo=self.server_info
            )
            return JSONRPCResponse(id=req.id, result=res.model_dump()).model_dump(exclude_none=True)

        elif req.method == "tools/list":
            res = ListToolsResult(tools=self.tools)
            return JSONRPCResponse(id=req.id, result=res.model_dump()).model_dump(exclude_none=True)

        elif req.method == "tools/call":
            params = req.params or {}
            tool_name = params.get("name")
            arguments = params.get("arguments", {})

            if tool_name == "get_clause":
                call_res = get_clause(
                    contract_id=arguments.get("contract_id", ""),
                    clause_number=arguments.get("clause_number"),
                    clause_type=arguments.get("clause_type")
                )
                return JSONRPCResponse(id=req.id, result=call_res.model_dump()).model_dump(exclude_none=True)

            elif tool_name == "get_definitions":
                call_res = get_definitions(
                    contract_id=arguments.get("contract_id", ""),
                    term=arguments.get("term")
                )
                return JSONRPCResponse(id=req.id, result=call_res.model_dump()).model_dump(exclude_none=True)

            else:
                return JSONRPCResponse(
                    id=req.id,
                    error=JSONRPCError(code=-32601, message=f"Tool '{tool_name}' not found on ClauseServer")
                ).model_dump(exclude_none=True)

        else:
            return JSONRPCResponse(
                id=req.id,
                error=JSONRPCError(code=-32601, message=f"Method '{req.method}' not implemented")
            ).model_dump(exclude_none=True)
