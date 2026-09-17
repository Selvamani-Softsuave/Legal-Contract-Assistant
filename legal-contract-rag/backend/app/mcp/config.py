"""
MCP Configuration Loader.
Parses JSON configuration files to register MCP servers dynamically.
Enables adding/removing MCP servers with 0 lines of code change in agent hosts.
"""

import json
import os
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class MCPServerConfig(BaseModel):
    id: str
    name: str
    endpoint: str = "in-process"
    server_type: str = "in_process"
    module: Optional[str] = None
    enabled: bool = True
    description: Optional[str] = None


class MCPRegistryConfig(BaseModel):
    servers: List[MCPServerConfig] = Field(default_factory=list)


def load_mcp_config(config_path_or_dict: Optional[object] = None) -> MCPRegistryConfig:
    """
    Load MCP Server configuration from a file path or dict.
    Defaults to loading from the config/ directory.
    """
    if isinstance(config_path_or_dict, dict):
        return MCPRegistryConfig(**config_path_or_dict)

    if isinstance(config_path_or_dict, str) and os.path.exists(config_path_or_dict):
        with open(config_path_or_dict, "r", encoding="utf-8") as f:
            data = json.load(f)
            return MCPRegistryConfig(**data)

    # Search default locations
    default_candidates = [
        "config/mcp_servers_all.json",
        "../config/mcp_servers_all.json",
        "/app/config/mcp_servers_all.json",
        "config/mcp_server1_only.json"
    ]
    for cand in default_candidates:
        if os.path.exists(cand):
            with open(cand, "r", encoding="utf-8") as f:
                data = json.load(f)
                return MCPRegistryConfig(**data)

    # Fallback default configuration
    return MCPRegistryConfig(
        servers=[
            MCPServerConfig(
                id="clause_server",
                name="Contract Clause & Definitions Server",
                module="app.mcp.servers.clause_server",
                enabled=True,
                description="Default in-process Clause Server"
            )
        ]
    )
