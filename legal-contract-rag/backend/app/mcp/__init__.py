"""
Model Context Protocol (MCP) Package for Legal Contract Assistant (Week 9 Module 5).
Implements JSON-RPC 2.0 message schemas, dynamic tool discovery, multi-server registration,
MCP gateway with unified audit & token scoping, and wire trace auditing.
"""

from backend.app.mcp.protocol import (
    JSONRPCRequest,
    JSONRPCResponse,
    JSONRPCError,
    MCPToolDefinition,
    InitializeParams,
    InitializeResult,
    ListToolsResult,
    CallToolParams,
    CallToolResult,
)
from backend.app.mcp.client import MCPClientManager
from backend.app.mcp.gateway import MCPGateway
from backend.app.agent.mcp_agent import MCPAgentHost

__all__ = [
    "JSONRPCRequest",
    "JSONRPCResponse",
    "JSONRPCError",
    "MCPToolDefinition",
    "InitializeParams",
    "InitializeResult",
    "ListToolsResult",
    "CallToolParams",
    "CallToolResult",
    "MCPClientManager",
    "MCPGateway",
    "MCPAgentHost",
]
