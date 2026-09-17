"""
Pydantic Schemas and DTOs for Model Context Protocol (MCP) REST Endpoints.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class MCPToolInputSchemaDTO(BaseModel):
    type: str = "object"
    properties: Dict[str, Any] = Field(default_factory=dict)
    required: Optional[List[str]] = None


class MCPToolDTO(BaseModel):
    name: str
    description: str
    inputSchema: MCPToolInputSchemaDTO
    server_id: Optional[str] = None


class MCPServerStatusDTO(BaseModel):
    id: str
    name: str
    enabled: bool
    tool_count: int
    tools: List[str]


class MCPDiscoveryResponseDTO(BaseModel):
    active_config: str
    server_count: int
    total_tools: int
    servers: List[MCPServerStatusDTO]
    tools: List[MCPToolDTO]


class MCPQueryRequestDTO(BaseModel):
    query: str
    contract_id: str = "CNT-MAIN-2024"
    server_config: Optional[str] = "all"  # "server1_only" or "all"


class MCPQueryResponseDTO(BaseModel):
    query: str
    contract_id: str
    tools_discovered_count: int
    tools_discovered: List[str]
    tools_invoked: List[str]
    reasoning_steps: List[Dict[str, Any]]
    final_answer: str


class MCPToolCallRequestDTO(BaseModel):
    tool_name: str
    arguments: Dict[str, Any] = Field(default_factory=dict)
    token: Optional[str] = None
    caller: Optional[str] = None
    role: Optional[str] = None


class MCPToolCallResponseDTO(BaseModel):
    content: List[Dict[str, Any]]
    isError: bool
    gateway_status: str
    audit_id: Optional[str] = None
    duration_ms: Optional[float] = None


class WirePacketDTO(BaseModel):
    timestamp: float
    iso_time: str
    direction: str
    server_id: str
    message_type: str
    raw_jsonrpc: Dict[str, Any]
    annotation: str
    host_model_boundary_note: Optional[str] = None


class MCPWireTraceResponseDTO(BaseModel):
    title: str
    protocol_version: str
    architecture_boundary_statement: str
    trace_summary: Dict[str, Any]
    packets: List[WirePacketDTO]


class AuditLogDTO(BaseModel):
    id: str
    timestamp: str
    caller: str
    role: str
    tool: str
    contract_id: Optional[str] = None
    status: str
    duration_ms: float
    error_message: Optional[str] = None
    arguments: Dict[str, Any]


class MCPErrorDemoResponseDTO(BaseModel):
    scenario: str
    error_path_before: Dict[str, Any]
    error_path_after: Dict[str, Any]
    transcript_before: str
    transcript_after: str
    model_recovery_success: bool
