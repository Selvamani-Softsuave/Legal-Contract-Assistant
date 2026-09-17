"""
MCP Wire Tracer.
Captures raw JSON-RPC 2.0 message exchanges across initialization, discovery, and tool execution.
Generates fully annotated wire traces for compliance deliverables (wire.json) and UI inspection.
"""

import json
import time
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class WirePacket(BaseModel):
    timestamp: float = Field(default_factory=time.time)
    iso_time: str = ""
    direction: str  # "client_to_server" or "server_to_client"
    server_id: str
    message_type: str  # "initialize_request", "initialize_response", "tools_list_request", "tools_list_response", "tools_call_request", "tools_call_response"
    raw_jsonrpc: Dict[str, Any]
    annotation: str
    host_model_boundary_note: Optional[str] = None


class MCPWireTracer:
    """Captures and stores in-memory JSON-RPC wire transactions."""

    def __init__(self):
        self.packets: List[WirePacket] = []

    def record_packet(
        self,
        server_id: str,
        direction: str,
        message_type: str,
        raw_jsonrpc: Dict[str, Any],
        annotation: str,
        host_model_boundary_note: Optional[str] = None
    ) -> WirePacket:
        now = time.time()
        iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now))
        packet = WirePacket(
            timestamp=now,
            iso_time=iso,
            direction=direction,
            server_id=server_id,
            message_type=message_type,
            raw_jsonrpc=raw_jsonrpc,
            annotation=annotation,
            host_model_boundary_note=host_model_boundary_note
        )
        self.packets.append(packet)
        return packet

    def clear(self):
        self.packets = []

    def get_packets(self) -> List[Dict[str, Any]]:
        return [p.model_dump() for p in self.packets]

    def export_annotated_trace(self) -> Dict[str, Any]:
        """Export the full structured wire trace required for Track F rubric."""
        return {
            "title": "Annotated Raw JSON-RPC 2.0 MCP Wire Trace",
            "protocol_version": "2024-11-05",
            "architecture_boundary_statement": (
                "MODEL CALL LOCATION: The LLM model call happens EXCLUSIVELY on the Agent Host side. "
                "The MCP servers provide structured data and tool execution without invoking LLMs."
            ),
            "trace_summary": {
                "total_packets": len(self.packets),
                "recorded_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            },
            "packets": [p.model_dump() for p in self.packets]
        }


# Global singleton instance for easy tracing
global_wire_tracer = MCPWireTracer()
