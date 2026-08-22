"""MCP Server — exposes UMOS capabilities as Model Context Protocol tools.

The MCP (Model Context Protocol) server allows Hermes Agent (or any
MCP-compatible host) to discover and call UMOS tools like fold,
collapse, compute, quantum, and cluster operations.

Protocol: JSON-RPC 2.0 over stdio (the standard MCP transport).
"""

from __future__ import annotations

import json
import sys
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from bridge.distributed.node import DistributedNode
from bridge.healer import SandboxExecutor
from bridge.hw_monitor import HWMonitor
from bridge.iep.schema import IntentAction, IntentMessage
from bridge.iep.dispatcher import IntentDispatcher
from bridge.llm import LLMConfig, chat
from umos_py._compat import safe_print as print


MCP_PROTOCOL_VERSION = "2025-03-26"


@dataclass
class MCPServerConfig:
    name: str = "umos"
    version: str = "0.5.0"
    protocol_version: str = MCP_PROTOCOL_VERSION


class UMOSMCPServer:
    """Lightweight MCP server exposing UMOS as tools for any MCP host.

    Usage:
        server = UMOSMCPServer()
        server.run_stdio()   # reads JSON-RPC from stdin, writes to stdout
    """

    def __init__(self, config: MCPServerConfig | None = None, node: DistributedNode | None = None):
        self.config = config or MCPServerConfig()
        self.dispatcher = IntentDispatcher(cluster_node=node)
        self.node = node
        self._initialized = False

    def handle_request(self, raw: str) -> str | None:
        try:
            msg = json.loads(raw)
        except json.JSONDecodeError:
            return self._error(None, -32700, "Parse error")

        req_id = msg.get("id")
        method = msg.get("method", "")
        params = msg.get("params", {})

        if method == "initialize":
            return self._handle_initialize(req_id, params)
        if method == "notifications/initialized":
            self._initialized = True
            return None  # notifications have no response
        if method == "tools/list":
            return self._handle_tools_list(req_id, params)
        if method == "tools/call":
            return self._handle_tools_call(req_id, params)
        if method == "resources/list":
            return self._result(req_id, {"resources": [
                {"uri": "umos://status", "name": "Node Status", "mimeType": "application/json"},
                {"uri": "umos://topology", "name": "Cluster Topology", "mimeType": "application/json"},
            ]})
        if method == "resources/read":
            return self._handle_resource_read(req_id, params)
        if method == "prompts/list":
            return self._result(req_id, {"prompts": [
                {
                    "name": "umos_fold_demo",
                    "description": "Demonstrate UMOS fold/collapse/expand",
                    "arguments": [
                        {"name": "bits", "description": "Comma-separated bits", "required": False},
                    ],
                },
            ]})
        if method == "prompts/get":
            return self._handle_prompt_get(req_id, params)
        if method == "shutdown":
            return self._result(req_id, {"shutdown": True})

        return self._error(req_id, -32601, "Method not found: {}".format(method))

    def run_stdio(self):
        print("[mcp] MCP server ready on stdio", file=sys.stderr)
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue
            resp = self.handle_request(line)
            if resp:
                sys.stdout.write(resp + "\n")
                sys.stdout.flush()

    # --- Handlers ---

    def _handle_initialize(self, req_id: Any, params: dict) -> str:
        client_info = params.get("clientInfo", {})
        print("[mcp] Client connected: {}".format(client_info.get("name", "?")))
        self._initialized = True
        return self._result(req_id, {
            "protocolVersion": MCP_PROTOCOL_VERSION,
            "serverInfo": {"name": self.config.name, "version": self.config.version},
            "capabilities": {
                "tools": {},
                "resources": {},
                "prompts": {},
            },
        })

    def _handle_tools_list(self, req_id: Any, params: dict) -> str:
        tools = [
            {
                "name": "umos_status",
                "description": "Get UMOS node status including CPU, RAM, precision, and capabilities",
                "inputSchema": {"type": "object", "properties": {}},
            },
            {
                "name": "umos_fold",
                "description": "Fold classical bits into quantum-like probability amplitudes using sine interpolation",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "bits": {
                            "type": "array",
                            "items": {"type": "integer"},
                            "description": "List of 0/1 bits to fold",
                        },
                    },
                    "required": ["bits"],
                },
            },
            {
                "name": "umos_collapse",
                "description": "Collapse folded amplitudes back to classical bits via threshold",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "folded": {
                            "type": "array",
                            "items": {"type": "number"},
                            "description": "Folded amplitude values",
                        },
                        "threshold": {
                            "type": "number",
                            "description": "Collapse threshold (default 0.5)",
                        },
                    },
                    "required": ["folded"],
                },
            },
            {
                "name": "umos_expand",
                "description": "Expand a signal by virtual interpolation factor",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "folded": {
                            "type": "array",
                            "items": {"type": "number"},
                        },
                        "factor": {
                            "type": "integer",
                            "description": "Expansion factor (default 2)",
                        },
                    },
                    "required": ["folded"],
                },
            },
            {
                "name": "umos_compute",
                "description": "Execute arbitrary Python code on UMOS with self-healing on failure",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "task": {
                            "type": "string",
                            "description": "Python code to execute. Assign result to variable 'result' or 'output'.",
                        },
                    },
                    "required": ["task"],
                },
            },
            {
                "name": "umos_heal",
                "description": "Send broken code to UMOS for automatic LLM-assisted repair",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "task": {
                            "type": "string",
                            "description": "The (broken) Python code to heal",
                        },
                    },
                    "required": ["task"],
                },
            },
            {
                "name": "umos_quantum_sample",
                "description": "Run a quantum circuit sample on available backend (Qiskit or CUDA-Q)",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "backend": {
                            "type": "string",
                            "enum": ["qiskit", "cudaq"],
                            "description": "Quantum backend to use",
                        },
                        "shots": {
                            "type": "integer",
                            "description": "Number of measurement shots",
                            "default": 1024,
                        },
                    },
                },
            },
            {
                "name": "umos_cluster_topology",
                "description": "Query the distributed cluster topology including alive peers and their weights",
                "inputSchema": {"type": "object", "properties": {}},
            },
            {
                "name": "umos_migrate",
                "description": "Migrate logical AI inference context to another cluster node",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "context": {
                            "type": "object",
                            "description": "Logical context key-value pairs to migrate",
                        },
                        "target": {
                            "type": "string",
                            "description": "Target node ID (optional, auto-selected if omitted)",
                        },
                    },
                    "required": ["context"],
                },
            },
        ]
        return self._result(req_id, {"tools": tools})

    def _handle_tools_call(self, req_id: Any, params: dict) -> str:
        name = params.get("name", "")
        args = params.get("arguments", {})

        action_map = {
            "umos_status": IntentAction.QUERY_STATUS,
            "umos_fold": IntentAction.FOLD,
            "umos_collapse": IntentAction.COLLAPSE,
            "umos_expand": IntentAction.EXPAND,
            "umos_compute": IntentAction.COMPUTE,
            "umos_heal": IntentAction.HEAL,
            "umos_cluster_topology": IntentAction.QUERY_TOPOLOGY,
            "umos_migrate": IntentAction.MIGRATE,
        }

        if name == "umos_quantum_sample":
            return self._handle_quantum_sample(req_id, args)

        action = action_map.get(name)
        if action is None:
            return self._error(req_id, -32602, "Unknown tool: {}".format(name))

        intent = IntentMessage(action=action, payload=args)
        result = self.dispatcher.dispatch(intent)

        return self._result(req_id, {
            "content": [{
                "type": "text",
                "text": json.dumps(result.to_dict(), indent=2),
            }],
        })

    def _handle_quantum_sample(self, req_id: Any, args: dict) -> str:
        backend = args.get("backend", "qiskit")
        shots = args.get("shots", 1024)
        bits = [1, 0, 1, 1, 0, 1, 0, 0, 1, 1]
        try:
            from quantum.cudaq_backend import (
                CUDAQBackend, is_available as cudaq_ok, make_fold_kernel,
            )
            if backend == "cudaq" and cudaq_ok():
                qb = CUDAQBackend()
                kernel_data = make_fold_kernel(bits)
                if kernel_data is None:
                    return self._error(req_id, -32000, "CUDA-Q fold kernel unavailable")
                result = qb.sample(kernel_data[0], *kernel_data[1:], shots=shots)
            else:
                from quantum.qunibit import QUnibit
                qu = QUnibit()
                qc = qu.fold_bits(bits, backend="qiskit")
                if qc is None:
                    return self._error(req_id, -32000, "Qiskit backend not available")
                result = qu.simulate(backend="qiskit", circuit=qc, shots=shots)
            return self._result(req_id, {
                "content": [{"type": "text", "text": json.dumps(result, indent=2)}],
            })
        except Exception as e:
            return self._error(req_id, -32000, str(e))

    def _handle_resource_read(self, req_id: Any, params: dict) -> str:
        uri = params.get("uri", "")
        if uri == "umos://status":
            intent = IntentMessage(action=IntentAction.QUERY_STATUS)
            result = self.dispatcher.dispatch(intent)
            return self._result(req_id, {
                "contents": [{
                    "uri": uri,
                    "mimeType": "application/json",
                    "text": json.dumps(result.to_dict(), indent=2),
                }],
            })
        if uri == "umos://topology":
            intent = IntentMessage(action=IntentAction.QUERY_TOPOLOGY)
            result = self.dispatcher.dispatch(intent)
            return self._result(req_id, {
                "contents": [{
                    "uri": uri,
                    "mimeType": "application/json",
                    "text": json.dumps(result.to_dict(), indent=2),
                }],
            })
        return self._error(req_id, -32602, "Resource not found: {}".format(uri))

    def _handle_prompt_get(self, req_id: Any, params: dict) -> str:
        name = params.get("name", "")
        args = params.get("arguments", {})
        if name == "umos_fold_demo":
            bits = args.get("bits", "1,0,1,1")
            return self._result(req_id, {
                "messages": [
                    {
                        "role": "user",
                        "content": {
                            "type": "text",
                            "text": (
                                "Let's demo UMOS. First fold the bits [{}] "
                                "into probability amplitudes, then expand the result by 2x."
                            ).format(bits),
                        },
                    },
                ],
            })
        return self._error(req_id, -32602, "Prompt not found: {}".format(name))

    # --- JSON-RPC helpers ---

    def _result(self, req_id: Any, result: Any) -> str:
        return json.dumps({"jsonrpc": "2.0", "id": req_id, "result": result})

    def _error(self, req_id: Any, code: int, message: str) -> str:
        return json.dumps({
            "jsonrpc": "2.0", "id": req_id,
            "error": {"code": code, "message": message},
        })


def main() -> int:
    print("[mcp] MCP Server demo")
    server = UMOSMCPServer()
    for method in ("initialize", "tools/list"):
        req = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": {}})
        resp = server.handle_request(req)
        print("[mcp] {} → {}".format(method, resp[:120] if resp else "None"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
