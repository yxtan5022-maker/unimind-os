"""IEP message schema — standardised JSON contract for Agent-to-Kernel.

Message format
--------------
{
  "version": "1.0",
  "intent": {
    "action": "compute | fold | expand | migrate | query | custom",
    "target": "classical | qiskit | cudaq | any",
    "payload": { ... },
    "priority": 0
  },
  "source": "astrbot | openai | manual",
  "session_id": "..."
}
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class IntentAction(str, Enum):
    COMPUTE = "compute"
    FOLD = "fold"
    EXPAND = "expand"
    COLLAPSE = "collapse"
    MIGRATE = "migrate"
    QUERY_TOPOLOGY = "query_topology"
    QUERY_STATUS = "query_status"
    HEAL = "heal"
    CUSTOM = "custom"


@dataclass
class ResourceCapability:
    backend: str = "classical"
    precision: str = "fp32"
    cpu_cores: int = 0
    memory_gb: float = 0.0
    has_quantum: bool = False
    has_cudaq: bool = False

    def to_dict(self) -> dict:
        return {
            "backend": self.backend,
            "precision": self.precision,
            "cpu_cores": self.cpu_cores,
            "memory_gb": self.memory_gb,
            "has_quantum": self.has_quantum,
            "has_cudaq": self.has_cudaq,
        }


@dataclass
class IntentMessage:
    version: str = "1.0"
    action: IntentAction = IntentAction.COMPUTE
    target: str = "any"
    payload: dict[str, Any] = field(default_factory=dict)
    priority: int = 0
    source: str = "manual"
    session_id: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "intent": {
                "action": self.action.value,
                "target": self.target,
                "payload": self.payload,
                "priority": self.priority,
            },
            "source": self.source,
            "session_id": self.session_id,
        }

    @staticmethod
    def from_dict(d: dict) -> IntentMessage:
        intent = d.get("intent", d)
        action_str = intent.get("action", "compute")
        try:
            action = IntentAction(action_str)
        except ValueError:
            action = IntentAction.CUSTOM
        return IntentMessage(
            version=d.get("version", "1.0"),
            action=action,
            target=intent.get("target", "any"),
            payload=intent.get("payload", {}),
            priority=intent.get("priority", 0),
            source=d.get("source", "manual"),
            session_id=d.get("session_id", ""),
        )


@dataclass
class IntentResponse:
    success: bool = True
    message: str = ""
    result: Any = None
    target_node: str = ""
    execution_time_ms: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "message": self.message,
            "result": str(self.result)[:500] if self.result is not None else None,
            "target_node": self.target_node,
            "execution_time_ms": round(self.execution_time_ms, 2),
        }
