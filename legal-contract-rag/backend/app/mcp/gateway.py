"""
MCP Gateway Module.
Provides centralized policy enforcement, Role-Based Access Control (RBAC) token scoping,
and structured audit logging across all incoming MCP tool invocations.
"""

import time
import uuid
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

try:
    from backend.app.mcp.client import MCPClientManager
except ImportError:
    from app.mcp.client import MCPClientManager


class AuditLogEntry(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    timestamp: str
    caller: str
    role: str
    tool: str
    contract_id: Optional[str] = None
    status: str  # "SUCCESS", "ERROR", "BLOCKED"
    duration_ms: float
    error_message: Optional[str] = None
    arguments: Dict[str, Any] = Field(default_factory=dict)


# Default Role-Based Access Scopes
ROLE_PERMISSIONS: Dict[str, List[str]] = {
    "admin": ["*"],
    "legal_counsel": [
        "get_clause",
        "get_definitions",
        "get_contract_metadata",
        "get_amendment_chain"
    ],
    "paralegal": [
        "get_clause",
        "get_definitions"
    ],
    "external_auditor": [
        "get_contract_metadata"
    ],
    "guest": []
}

# API Token to Role mapping for demonstration & test harness
TOKEN_ROLES: Dict[str, Dict[str, str]] = {
    "token_admin_001": {"caller": "counsel_lead@enterprise.com", "role": "admin"},
    "token_counsel_002": {"caller": "senior_attorney@firm.com", "role": "legal_counsel"},
    "token_paralegal_003": {"caller": "associate_legal@firm.com", "role": "paralegal"},
    "token_auditor_004": {"caller": "compliance_auditor@kpmg.com", "role": "external_auditor"},
    "token_guest_005": {"caller": "anonymous_guest@public.com", "role": "guest"}
}


class MCPGateway:
    """Enterprise Gateway mediating MCP tool execution with RBAC and Unified Audit Logging."""

    def __init__(self, client_manager: MCPClientManager):
        self.client_manager = client_manager
        self.audit_logs: List[AuditLogEntry] = []

    def verify_permission(self, role: str, tool_name: str) -> bool:
        """Verify whether a given role is authorized to execute the tool."""
        allowed_tools = ROLE_PERMISSIONS.get(role, [])
        if "*" in allowed_tools:
            return True
        return tool_name in allowed_tools

    def execute_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        token: Optional[str] = None,
        caller: Optional[str] = None,
        role: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute tool through security gateway, enforcing RBAC and generating structured audit logs.
        """
        start_time = time.time()
        iso_time = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(start_time))
        
        # 1. Resolve Identity and Role
        resolved_caller = caller or "system_agent"
        resolved_role = role or "legal_counsel"
        
        if token and token in TOKEN_ROLES:
            resolved_caller = TOKEN_ROLES[token]["caller"]
            resolved_role = TOKEN_ROLES[token]["role"]

        contract_id = arguments.get("contract_id")

        # 2. RBAC Policy Check
        if not self.verify_permission(resolved_role, tool_name):
            duration_ms = round((time.time() - start_time) * 1000, 2)
            err_msg = f"RBAC Access Denied: Role '{resolved_role}' does not have permission to execute tool '{tool_name}'."
            
            audit_entry = AuditLogEntry(
                timestamp=iso_time,
                caller=resolved_caller,
                role=resolved_role,
                tool=tool_name,
                contract_id=contract_id,
                status="BLOCKED",
                duration_ms=duration_ms,
                error_message=err_msg,
                arguments=arguments
            )
            self.audit_logs.append(audit_entry)

            return {
                "content": [{"type": "text", "text": err_msg}],
                "isError": True,
                "gateway_status": "BLOCKED",
                "audit_id": audit_entry.id
            }

        # 3. Forward to MCP Client Manager
        try:
            result = self.client_manager.call_tool(tool_name, arguments)
            duration_ms = round((time.time() - start_time) * 1000, 2)
            is_error = result.get("isError", False)
            status = "ERROR" if is_error else "SUCCESS"
            err_text = None
            if is_error and result.get("content"):
                err_text = result["content"][0].get("text")

            audit_entry = AuditLogEntry(
                timestamp=iso_time,
                caller=resolved_caller,
                role=resolved_role,
                tool=tool_name,
                contract_id=contract_id,
                status=status,
                duration_ms=duration_ms,
                error_message=err_text,
                arguments=arguments
            )
            self.audit_logs.append(audit_entry)

            return {
                **result,
                "gateway_status": status,
                "audit_id": audit_entry.id,
                "duration_ms": duration_ms
            }

        except Exception as e:
            duration_ms = round((time.time() - start_time) * 1000, 2)
            audit_entry = AuditLogEntry(
                timestamp=iso_time,
                caller=resolved_caller,
                role=resolved_role,
                tool=tool_name,
                contract_id=contract_id,
                status="ERROR",
                duration_ms=duration_ms,
                error_message=str(e),
                arguments=arguments
            )
            self.audit_logs.append(audit_entry)

            return {
                "content": [{"type": "text", "text": f"Gateway Execution Error: {str(e)}"}],
                "isError": True,
                "gateway_status": "ERROR",
                "audit_id": audit_entry.id
            }

    def get_audit_logs(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Retrieve recent gateway audit log entries."""
        return [entry.model_dump() for entry in reversed(self.audit_logs[-limit:])]

    def clear_audit_logs(self):
        self.audit_logs = []
