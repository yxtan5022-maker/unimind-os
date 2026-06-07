"""ACP Protocol Adapter — Hermes Agent communication.

Implements the Agent Communication Protocol (ACP) so Hermes Agent
can discover, authenticate, and interact with UMOS as a peer agent.

ACP uses JSON-RPC 2.0 over stdio (or TCP) with agent-specific methods
like session/prompt for task delegation.
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


ACP_JSON_RPC_VERSION = "2.0"


@dataclass
class ACPMessage:
    id: str
    method: str
    params: dict[str, Any] = field(default_factory=dict)
    jsonrpc: str = ACP_JSON_RPC_VERSION


@dataclass
class ACPSession:
    session_id: str
    agent_id: str
    capabilities: dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)


class HermesACPAdapter:
    """ACP protocol handler that translates Hermes ACP calls into UMOS IEP dispatches.

    The adapter runs as a stdio JSON-RPC 2.0 server, compatible with
    Hermes Agent's ACP transport. Hermes can spawn a subprocess running
    this adapter and communicate via stdin/stdout.
    """

    def __init__(self, node: DistributedNode | None = None):
        self.dispatcher = IntentDispatcher(cluster_node=node)
        self.node = node
        self.sessions: dict[str, ACPSession] = {}
        self.executor = SandboxExecutor()

    # --- JSON-RPC dispatch ---

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
        if method == "authenticate":
            return self._handle_authenticate(req_id, params)
        if method == "session/new":
            return self._handle_session_new(req_id, params)
        if method == "session/prompt":
            return self._handle_session_prompt(req_id, params)
        if method == "tools/list":
            return self._handle_tools_list(req_id, params)
        if method == "tools/call":
            return self._handle_tools_call(req_id, params)
        if method == "shutdown":
            return self._result(req_id, {"shutdown": True})

        return self._error(req_id, -32601, "Method not found: {}".format(method))

    def run_stdio(self):
        """Read JSON-RPC requests from stdin, write responses to stdout."""
        print("[acp] ACP adapter ready on stdio", file=sys.stderr)
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
        return self._result(req_id, {
            "protocol_version": ACP_JSON_RPC_VERSION,
            "agent_name": "UMOS",
            "agent_version": "0.5.0",
            "capabilities": {
                "fold": True,
                "collapse": True,
                "expand": True,
                "compute": True,
                "quantum": True,
                "cluster": self.node is not None,
                "heal": True,
                "migrate": True,
            },
        })

    def _handle_authenticate(self, req_id: Any, params: dict) -> str:
        token = params.get("token", "")
        # For now, accept any non-empty token
        if token:
            return self._result(req_id, {"authenticated": True, "agent": "UMOS"})
        return self._error(req_id, -32001, "Authentication required")

    def _handle_session_new(self, req_id: Any, params: dict) -> str:
        agent_id = params.get("agent_id", "unknown")
        session_id = "umos-{}".format(uuid.uuid4().hex[:12])
        self.sessions[session_id] = ACPSession(
            session_id=session_id,
            agent_id=agent_id,
            capabilities=params.get("capabilities", {}),
        )
        return self._result(req_id, {
            "session_id": session_id,
            "created": self.sessions[session_id].created_at,
        })

    def _handle_session_prompt(self, req_id: Any, params: dict) -> str:
        session_id = params.get("session_id", "")
        session = self.sessions.get(session_id)
        if not session:
            return self._error(req_id, -32002, "Session not found: {}".format(session_id))

        prompt = params.get("prompt", "")
        action_hint = params.get("action", "custom")
        payload = params.get("payload", {})
        payload["task"] = payload.get("task", prompt)

        intent = IntentMessage(
            action=IntentAction(action_hint) if action_hint in IntentAction._value2member_map_ else IntentAction.CUSTOM,
            payload=payload,
            session_id=session_id,
        )
        result = self.dispatcher.dispatch(intent)
        return self._result(req_id, {
            "success": result.success,
            "message": result.message,
            "result": result.result,
            "execution_time_ms": result.execution_time_ms,
        })

    def _handle_tools_list(self, req_id: Any, params: dict) -> str:
        tools = [
            {
                "name": "umos_status",
                "description": "Get UMOS node status (CPU, RAM, precision, capabilities)",
                "input_schema": {"type": "object", "properties": {}},
            },
            {
                "name": "umos_fold",
                "description": "Fold classical bits into quantum-like amplitudes",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "bits": {"type": "array", "items": {"type": "integer"}},
                    },
                    "required": ["bits"],
                },
            },
            {
                "name": "umos_collapse",
                "description": "Collapse folded signal back to bits",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "folded": {"type": "array", "items": {"type": "number"}},
                        "threshold": {"type": "number"},
                    },
                    "required": ["folded"],
                },
            },
            {
                "name": "umos_expand",
                "description": "Virtually expand a signal by a factor",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "folded": {"type": "array", "items": {"type": "number"}},
                        "factor": {"type": "integer"},
                    },
                    "required": ["folded"],
                },
            },
            {
                "name": "umos_compute",
                "description": "Execute Python code on UMOS (with self-healing)",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "task": {"type": "string"},
                    },
                    "required": ["task"],
                },
            },
            {
                "name": "umos_heal",
                "description": "Attempt to auto-heal broken code",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "task": {"type": "string"},
                    },
                    "required": ["task"],
                },
            },
            {
                "name": "umos_quantum_sample",
                "description": "Run a quantum circuit sample (Qiskit or CUDA-Q if available)",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "backend": {"type": "string", "enum": ["qiskit", "cudaq"]},
                        "shots": {"type": "integer"},
                    },
                },
            },
            {
                "name": "umos_cluster_topology",
                "description": "Query cluster peer topology",
                "input_schema": {"type": "object", "properties": {}},
            },
            {
                "name": "umos_migrate",
                "description": "Migrate logical context to another cluster node",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "context": {"type": "object"},
                        "target": {"type": "string"},
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
            "umos_quantum_sample": IntentAction.CUSTOM,
            "umos_cluster_topology": IntentAction.QUERY_TOPOLOGY,
            "umos_migrate": IntentAction.MIGRATE,
        }

        action = action_map.get(name)
        if action is None:
            return self._error(req_id, -32602, "Unknown tool: {}".format(name))

        intent = IntentMessage(action=action, payload=args)
        result = self.dispatcher.dispatch(intent)
        return self._result(req_id, {
            "success": result.success,
            "content": [{"type": "text", "text": json.dumps({
                "message": result.message,
                "result": result.result,
                "execution_time_ms": result.execution_time_ms,
            })}],
        })

    # --- JSON-RPC helpers ---

    def _result(self, req_id: Any, result: Any) -> str:
        return json.dumps({"jsonrpc": "2.0", "id": req_id, "result": result})

    def _error(self, req_id: Any, code: int, message: str) -> str:
        return json.dumps({
            "jsonrpc": "2.0", "id": req_id,
            "error": {"code": code, "message": message},
        })


def main() -> int:
    print("[acp] Hermes ACP Adapter demo")
    adapter = HermesACPAdapter()
    # demo a few methods
    for method in ("initialize", "tools/list"):
        req = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": {}})
        resp = adapter.handle_request(req)
        print("[acp] {} → {}".format(method, resp[:120] if resp else "None"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
