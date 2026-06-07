"""Hermes Agent Integration — ACP adapter, MCP server, and skill definitions.

Allows UMOS to be discovered and used by Hermes Agent as:
- An MCP server (exposes UMOS tools via Model Context Protocol)
- An ACP peer (agent-to-agent communication)
- A downloadable skill (SKILL.md for the Skills Hub)
"""

from bridge.hermes.adapter import (
    HermesACPAdapter, ACPMessage, ACPSession,
)
from bridge.hermes.mcp_server import (
    UMOSMCPServer, MCPServerConfig,
)

__all__ = [
    "HermesACPAdapter", "ACPMessage", "ACPSession",
    "UMOSMCPServer", "MCPServerConfig",
]
