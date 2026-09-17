"""
Model Context Protocol (MCP) JSON-RPC 2.0 Protocol Specifications and Schemas.
Implements the core MCP data models and message structures for tools and initialization.
"""

from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field


class JSONRPCError(BaseModel):
    code: int
    message: str
    data: Optional[Any] = None


class JSONRPCRequest(BaseModel):
    jsonrpc: str = "2.0"
    id: Union[str, int]
    method: str
    params: Optional[Dict[str, Any]] = None


class JSONRPCResponse(BaseModel):
    jsonrpc: str = "2.0"
    id: Optional[Union[str, int]] = None
    result: Optional[Any] = None
    error: Optional[JSONRPCError] = None


class ServerInfo(BaseModel):
    name: str
    version: str = "1.0.0"


class ServerCapabilities(BaseModel):
    tools: Dict[str, Any] = Field(default_factory=lambda: {"listChanged": False})
    resources: Optional[Dict[str, Any]] = None
    prompts: Optional[Dict[str, Any]] = None


class InitializeParams(BaseModel):
    protocolVersion: str = "2024-11-05"
    capabilities: Dict[str, Any] = Field(default_factory=dict)
    clientInfo: Dict[str, str] = Field(default_factory=lambda: {"name": "LegalMCPAgentHost", "version": "1.0.0"})


class InitializeResult(BaseModel):
    protocolVersion: str = "2024-11-05"
    capabilities: ServerCapabilities = Field(default_factory=ServerCapabilities)
    serverInfo: ServerInfo


class ToolInputProperty(BaseModel):
    type: str
    description: Optional[str] = None
    enum: Optional[List[str]] = None
    items: Optional[Dict[str, Any]] = None


class ToolInputSchema(BaseModel):
    type: str = "object"
    properties: Dict[str, Any] = Field(default_factory=dict)
    required: Optional[List[str]] = None


class MCPToolDefinition(BaseModel):
    name: str
    description: str
    inputSchema: ToolInputSchema


class ListToolsResult(BaseModel):
    tools: List[MCPToolDefinition]
    nextCursor: Optional[str] = None


class CallToolParams(BaseModel):
    name: str
    arguments: Dict[str, Any] = Field(default_factory=dict)


class ToolContent(BaseModel):
    type: str = "text"
    text: str


class CallToolResult(BaseModel):
    content: List[ToolContent] = Field(default_factory=list)
    isError: bool = False
