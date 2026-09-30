"""
MCP Server 2: Contract Repository & Metadata Server.
Exposes tools for retrieving contract metadata, governing laws, counterparties, and amendment chains.
Demonstrates zero-code agent extensibility when combined with Server 1 via config.
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

SERVER_INFO = ServerInfo(name="Contract Repository & Metadata Server", version="1.0.0")

MOCK_METADATA = {
    "CNT-MAIN-2024": {
        "contract_id": "CNT-MAIN-2024",
        "title": "Master Services Agreement",
        "parties": ["Acme Global Technologies Inc.", "Zeta Cloud Services LLC"],
        "effective_date": "2024-01-15",
        "expiration_date": "2027-01-14",
        "governing_law": "State of Delaware, United States",
        "status": "Active (Amended)",
        "total_value_usd": 1250000.00,
        "signatories": [
            {"name": "Alice Sterling", "role": "VP Procurement, Acme Global"},
            {"name": "Robert Vance", "role": "Chief Commercial Officer, Zeta Cloud"}
        ],
        "amendment_ids": ["CNT-AMD-2024-01"]
    },
    "CNT-AMD-2024-01": {
        "contract_id": "CNT-AMD-2024-01",
        "title": "Amendment No. 1 to Master Services Agreement",
        "parties": ["Acme Global Technologies Inc.", "Zeta Cloud Services LLC"],
        "effective_date": "2024-06-01",
        "parent_contract_id": "CNT-MAIN-2024",
        "governing_law": "State of Delaware, United States",
        "status": "Active",
        "purpose": "Relocation of dispute resolution protocol to AAA arbitration and increase of SLA rebate threshold."
    }
}

MOCK_AMENDMENTS = {
    "CNT-MAIN-2024": [
        {
            "sequence": 1,
            "amendment_id": "CNT-AMD-2024-01",
            "title": "Dispute Resolution & SLA Update Amendment",
            "effective_date": "2024-06-01",
            "summary": "Supersedes former Clause 12.4; mandates 14-day senior executive escalation followed by AAA binding arbitration in Wilmington, DE.",
            "affected_sections": ["Clause 12.4 (Replaced)", "Schedule B (SLA Updated)"]
        }
    ]
}


def get_contract_metadata(contract_id: str) -> CallToolResult:
    """
    Retrieve comprehensive metadata for a contract including parties, effective date, governing law, total contract value, lifecycle status, and linked parent/subsidiary agreement IDs.
    Use this tool to identify counterparties, jurisdiction rules, or active contract status.
    Provide the contract_id (e.g. 'CNT-MAIN-2024').
    """
    meta = MOCK_METADATA.get(contract_id)
    if not meta:
        avail = list(MOCK_METADATA.keys())
        err_text = (
            f"Contract metadata not found for '{contract_id}'. "
            f"Available registered contracts: {', '.join(avail)}. "
            "Please check the ID or verify if it is an unindexed document."
        )
        return CallToolResult(content=[ToolContent(text=err_text)], isError=True)

    formatted_json = json.dumps(meta, indent=2)
    return CallToolResult(
        content=[ToolContent(text=f"Contract Metadata for {contract_id}:\n{formatted_json}")],
        isError=False
    )


def get_amendment_chain(contract_id: str) -> CallToolResult:
    """
    Retrieve the chronological amendment and addenda history for a master agreement.
    Use this tool to track superseded terms, dispute escalation changes, scope modifications, or current active versions across related legal instruments.
    Provide the master contract_id (e.g. 'CNT-MAIN-2024').
    """
    chain = MOCK_AMENDMENTS.get(contract_id)
    if not chain:
        if contract_id in MOCK_METADATA:
            return CallToolResult(
                content=[ToolContent(text=f"Contract '{contract_id}' exists as a standalone agreement with no recorded amendments or addenda.")],
                isError=False
            )
        return CallToolResult(
            content=[ToolContent(text=f"Master agreement '{contract_id}' not found in the Amendment Registry. Available master IDs: {', '.join(MOCK_AMENDMENTS.keys())}")],
            isError=True
        )

    output = [f"Amendment Chain History for Master Agreement '{contract_id}':"]
    for amd in chain:
        output.append(
            f"\n• Sequence #{amd['sequence']}: {amd['amendment_id']} - {amd['title']}\n"
            f"  Effective Date: {amd['effective_date']}\n"
            f"  Summary: {amd['summary']}\n"
            f"  Affected Sections: {', '.join(amd['affected_sections'])}"
        )
    return CallToolResult(content=[ToolContent(text="\n".join(output))], isError=False)


TOOLS = [
    MCPToolDefinition(
        name="get_contract_metadata",
        description=(
            "Retrieve comprehensive metadata for a contract including parties, effective date, governing law, "
            "total contract value, lifecycle status, and linked parent/subsidiary agreement IDs. "
            "Use this tool to identify counterparties, jurisdiction rules, or active contract status. "
            "Provide the contract_id (e.g. 'CNT-MAIN-2024')."
        ),
        inputSchema=ToolInputSchema(
            type="object",
            properties={
                "contract_id": {
                    "type": "string",
                    "description": "Unique identifier of the contract to inspect (e.g. 'CNT-MAIN-2024')"
                }
            },
            required=["contract_id"]
        )
    ),
    MCPToolDefinition(
        name="get_amendment_chain",
        description=(
            "Retrieve the chronological amendment and addenda history for a master agreement. "
            "Use this tool to track superseded terms, dispute escalation changes, scope modifications, "
            "or current active versions across related legal instruments. "
            "Provide the master contract_id (e.g. 'CNT-MAIN-2024')."
        ),
        inputSchema=ToolInputSchema(
            type="object",
            properties={
                "contract_id": {
                    "type": "string",
                    "description": "Unique master agreement ID (e.g. 'CNT-MAIN-2024')"
                }
            },
            required=["contract_id"]
        )
    )
]


class RepoServer:
    """In-process and JSON-RPC dispatchable MCP Server for Contract Repository & Metadata."""

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

            if tool_name == "get_contract_metadata":
                call_res = get_contract_metadata(
                    contract_id=arguments.get("contract_id", "")
                )
                return JSONRPCResponse(id=req.id, result=call_res.model_dump()).model_dump(exclude_none=True)

            elif tool_name == "get_amendment_chain":
                call_res = get_amendment_chain(
                    contract_id=arguments.get("contract_id", "")
                )
                return JSONRPCResponse(id=req.id, result=call_res.model_dump()).model_dump(exclude_none=True)

            else:
                return JSONRPCResponse(
                    id=req.id,
                    error=JSONRPCError(code=-32601, message=f"Tool '{tool_name}' not found on RepoServer")
                ).model_dump(exclude_none=True)

        else:
            return JSONRPCResponse(
                id=req.id,
                error=JSONRPCError(code=-32601, message=f"Method '{req.method}' not implemented")
            ).model_dump(exclude_none=True)
