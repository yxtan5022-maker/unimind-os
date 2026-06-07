"""Message types for distributed UMOS cluster communication.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class MessageType(str, Enum):
    HEARTBEAT = "heartbeat"
    PEER_JOIN = "peer_join"
    PEER_LEAVE = "peer_leave"
    TASK_OFFER = "task_offer"
    TASK_ACCEPT = "task_accept"
    TASK_REJECT = "task_reject"
    TASK_COMPLETE = "task_complete"
    LOGICAL_MIGRATE = "logical_migrate"
    STATE_SYNC = "state_sync"


@dataclass
class PeerInfo:
    node_id: str
    host: str
    port: int
    listen_port: int = 0
    cpu_load: float = 0.0
    memory_available_gb: float = 0.0
    memory_percent: float = 0.0
    precision: str = "fp32"
    available_backends: list[str] = field(default_factory=lambda: ["classical"])
    logical_weight: float = 1.0
    last_seen: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "node_id": self.node_id,
            "host": self.host,
            "port": self.port,
            "listen_port": self.listen_port,
            "cpu_load": self.cpu_load,
            "memory_available_gb": round(self.memory_available_gb, 2),
            "memory_percent": round(self.memory_percent, 1),
            "precision": self.precision,
            "available_backends": self.available_backends,
            "logical_weight": self.logical_weight,
        }

    @staticmethod
    def from_dict(d: dict) -> PeerInfo:
        return PeerInfo(
            node_id=d.get("node_id", ""),
            host=d.get("host", "0.0.0.0"),
            port=d.get("port", 0),
            listen_port=d.get("listen_port", 0),
            cpu_load=d.get("cpu_load", 0.0),
            memory_available_gb=d.get("memory_available_gb", 0.0),
            memory_percent=d.get("memory_percent", 0.0),
            precision=d.get("precision", "fp32"),
            available_backends=d.get("available_backends", ["classical"]),
            logical_weight=d.get("logical_weight", 1.0),
        )


@dataclass
class ServiceAnnouncement:
    msg_type: MessageType = MessageType.HEARTBEAT
    sender: PeerInfo = field(default_factory=PeerInfo)
    timestamp: float = 0.0
    msg_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])

    def to_dict(self) -> dict[str, Any]:
        return {
            "msg_type": self.msg_type.value,
            "sender": self.sender.to_dict(),
            "timestamp": self.timestamp or __import__("time").time(),
            "msg_id": self.msg_id,
        }

    @staticmethod
    def from_dict(d: dict) -> ServiceAnnouncement:
        return ServiceAnnouncement(
            msg_type=MessageType(d.get("msg_type", "heartbeat")),
            sender=PeerInfo.from_dict(d.get("sender", {})),
            timestamp=d.get("timestamp", 0.0),
            msg_id=d.get("msg_id", ""),
        )


@dataclass
class TaskOffer:
    task_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    source_node: str = ""
    target_node: str = ""
    action: str = ""
    payload: dict[str, Any] = field(default_factory=dict)
    logical_context: dict[str, Any] = field(default_factory=dict)
    priority: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "source_node": self.source_node,
            "target_node": self.target_node,
            "action": self.action,
            "payload": self.payload,
            "logical_context": self.logical_context,
            "priority": self.priority,
        }
