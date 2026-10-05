"""
MCP Client Manager.
Manages connections to multiple MCP servers, performs initialization handshakes,
discovers available tools dynamically, and routes tool calls over JSON-RPC 2.0.
Integrates with MCPWireTracer to log all wire packets.
"""

import uuid
from typing import Any, Dict, List, Optional, Tuple

from backend.app.mcp.config import MCPRegistryConfig, MCPServerConfig, load_mcp_config
from backend.app.mcp.protocol import (
    JSONRPCRequest,
    JSONRPCResponse,
    MCPToolDefinition,
    CallToolResult,
    ToolContent
)
from backend.app.mcp.servers.clause_server import ClauseServer
from backend.app.mcp.servers.repo_server import RepoServer
from backend.app.mcp.wire_tracer import MCPWireTracer, global_wire_tracer


class MCPClientManager:
    """Manages MCP Server connections, dynamic tool discovery, and JSON-RPC dispatch."""

    def __init__(self, config: Optional[MCPRegistryConfig] = None, tracer: Optional[MCPWireTracer] = None):
        self.config = config or load_mcp_config()
        self.tracer = tracer or global_wire_tracer
        self.server_instances: Dict[str, Any] = {}
        self.server_metadata: Dict[str, Dict[str, Any]] = {}
        self.tool_to_server_map: Dict[str, str] = {}
        self.tools_registry: Dict[str, MCPToolDefinition] = {}
        self._initialize_servers()

    def _get_server_instance(self, server_cfg: MCPServerConfig) -> Any:
        """Instantiate or retrieve server handler."""
        if server_cfg.id == "clause_server":
            return ClauseServer()
        elif server_cfg.id == "repo_server":
            return RepoServer()
        else:
            if server_cfg.module in ["backend.app.mcp.servers.clause_server", "app.mcp.servers.clause_server"]:
                return ClauseServer()
            elif server_cfg.module in ["backend.app.mcp.servers.repo_server", "app.mcp.servers.repo_server"]:
                return RepoServer()
            raise ValueError(f"Unknown MCP server module/id: {server_cfg.id}")

    def _initialize_servers(self):
        """Perform MCP JSON-RPC initialization handshake and tool discovery for all configured servers."""
        self.server_instances.clear()
        self.tool_to_server_map.clear()
        self.tools_registry.clear()

        for server_cfg in self.config.servers:
            if not server_cfg.enabled:
                continue

            instance = self._get_server_instance(server_cfg)
            self.server_instances[server_cfg.id] = instance

            # 1. JSON-RPC Handshake: initialize
            req_id_init = str(uuid.uuid4())[:8]
            init_req_payload = {
                "jsonrpc": "2.0",
                "id": req_id_init,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "LegalMCPAgentHost", "version": "1.0.0"}
                }
            }

            self.tracer.record_packet(
                server_id=server_cfg.id,
                direction="client_to_server",
                message_type="initialize_request",
                raw_jsonrpc=init_req_payload,
                annotation=f"Client sends protocol handshake to '{server_cfg.name}' requesting MCP version 2024-11-05.",
                host_model_boundary_note="Agent Host prepares connection before invoking LLM."
            )

            init_res_payload = instance.handle_jsonrpc(init_req_payload)

            self.tracer.record_packet(
                server_id=server_cfg.id,
                direction="server_to_client",
                message_type="initialize_response",
                raw_jsonrpc=init_res_payload,
                annotation=f"Server '{server_cfg.id}' accepts handshake, returning protocolVersion and capabilities.",
                host_model_boundary_note="Server ready for discovery. No model invocation occurs on server."
            )

            self.server_metadata[server_cfg.id] = init_res_payload.get("result", {})

            # 2. JSON-RPC Tool Discovery: tools/list
            req_id_list = str(uuid.uuid4())[:8]
            list_req_payload = {
                "jsonrpc": "2.0",
                "id": req_id_list,
                "method": "tools/list",
                "params": {}
            }

            self.tracer.record_packet(
                server_id=server_cfg.id,
                direction="client_to_server",
                message_type="tools_list_request",
                raw_jsonrpc=list_req_payload,
                annotation=f"Client queries available tools from '{server_cfg.name}'.",
                host_model_boundary_note="Host discovers tool capabilities to bind into the agent prompt/schema."
            )

            list_res_payload = instance.handle_jsonrpc(list_req_payload)

            self.tracer.record_packet(
                server_id=server_cfg.id,
                direction="server_to_client",
                message_type="tools_list_response",
                raw_jsonrpc=list_res_payload,
                annotation=f"Server '{server_cfg.id}' returns tool schemas and prompt-styled docstrings.",
                host_model_boundary_note="Host parses tool schemas. Host will format these into OpenAI/Anthropic tool schemas for the LLM."
            )

            # Register discovered tools
            tools_list = list_res_payload.get("result", {}).get("tools", [])
            for t_dict in tools_list:
                tool_def = MCPToolDefinition(**t_dict)
                self.tools_registry[tool_def.name] = tool_def
                self.tool_to_server_map[tool_def.name] = server_cfg.id

    def list_tools(self) -> List[MCPToolDefinition]:
        """Return all discovered MCP tools across all active servers."""
        return list(self.tools_registry.values())

    def get_tool_names(self) -> List[str]:
        """Return list of tool names currently discovered."""
        return list(self.tools_registry.keys())

    def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool via its target MCP server with full JSON-RPC wire tracing."""
        server_id = self.tool_to_server_map.get(tool_name)
        if not server_id or server_id not in self.server_instances:
            return {
                "content": [{"type": "text", "text": f"Error: Tool '{tool_name}' not found on any active MCP server."}],
                "isError": True
            }

        server_instance = self.server_instances[server_id]
        req_id_call = str(uuid.uuid4())[:8]
        call_req_payload = {
            "jsonrpc": "2.0",
            "id": req_id_call,
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            }
        }

        self.tracer.record_packet(
            server_id=server_id,
            direction="client_to_server",
            message_type="tools_call_request",
            raw_jsonrpc=call_req_payload,
            annotation=f"Host calls tool '{tool_name}' on server '{server_id}' with arguments: {arguments}.",
            host_model_boundary_note="LLM decided to call this tool. Host dispatched the JSON-RPC request to MCP server."
        )

        call_res_payload = server_instance.handle_jsonrpc(call_req_payload)

        self.tracer.record_packet(
            server_id=server_id,
            direction="server_to_client",
            message_type="tools_call_response",
            raw_jsonrpc=call_res_payload,
            annotation=f"Server '{server_id}' returns execution result for tool '{tool_name}'.",
            host_model_boundary_note="MCP server finished execution. Host receives result and injects it back into LLM context."
        )

        if "result" in call_res_payload:
            return call_res_payload["result"]
        elif "error" in call_res_payload:
            return {
                "content": [{"type": "text", "text": f"MCP Error {call_res_payload['error'].get('code')}: {call_res_payload['error'].get('message')}"}],
                "isError": True
            }
        return {"content": [{"type": "text", "text": "Empty result"}], "isError": True}

    def reload_config(self, new_config: MCPRegistryConfig):
        """Dynamically reload MCP servers from a new configuration."""
        self.config = new_config
        self._initialize_servers()
