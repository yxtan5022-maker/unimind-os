"""Cluster-wide peer state management.
"""

from __future__ import annotations

import time
from typing import Any

from bridge.distributed.protocol import PeerInfo


PEER_TIMEOUT_SECONDS = 15.0


class PeerState:
    def __init__(self, info: PeerInfo):
        self.info = info
        self.first_seen = time.time()
        self.last_seen = time.time()
        self.consecutive_misses = 0

    def update(self, info: PeerInfo) -> None:
        self.info = info
        self.last_seen = time.time()
        self.consecutive_misses = 0

    def mark_missed(self) -> None:
        self.consecutive_misses += 1

    @property
    def is_alive(self) -> bool:
        age = time.time() - self.last_seen
        return age < PEER_TIMEOUT_SECONDS and self.consecutive_misses < 3

    @property
    def logical_weight(self) -> float:
        load = max(self.info.cpu_load, self.info.memory_percent)
        if load >= 85:
            return 0.2
        if load >= 65:
            return 0.5
        if load >= 40:
            return 0.8
        return 1.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "info": self.info.to_dict(),
            "first_seen": self.first_seen,
            "last_seen": self.last_seen,
            "is_alive": self.is_alive,
            "logical_weight": self.logical_weight,
        }


class ClusterState:
    def __init__(self):
        self._peers: dict[str, PeerState] = {}

    def upsert(self, info: PeerInfo) -> None:
        if info.node_id in self._peers:
            self._peers[info.node_id].update(info)
        else:
            self._peers[info.node_id] = PeerState(info)

    def remove(self, node_id: str) -> None:
        self._peers.pop(node_id, None)

    def get(self, node_id: str) -> PeerState | None:
        return self._peers.get(node_id)

    @property
    def alive_peers(self) -> list[PeerState]:
        now = time.time()
        result = []
        for ps in self._peers.values():
            age = now - ps.last_seen
            if age < PEER_TIMEOUT_SECONDS and ps.consecutive_misses < 3:
                result.append(ps)
            else:
                ps.consecutive_misses += 1
        return result

    @property
    def all(self) -> list[PeerState]:
        return list(self._peers.values())

    def best_target(self, exclude: set[str] | None = None) -> PeerState | None:
        exclude = exclude or set()
        candidates = [p for p in self.alive_peers if p.info.node_id not in exclude]
        if not candidates:
            return None
        candidates.sort(key=lambda p: p.logical_weight, reverse=True)
        return candidates[0]

    def cluster_summary(self) -> dict[str, Any]:
        alive = self.alive_peers
        return {
            "total_peers": len(self._peers),
            "alive_peers": len(alive),
            "peers": [p.info.to_dict() for p in alive],
            "avg_cpu": sum(p.info.cpu_load for p in alive) / max(len(alive), 1),
            "avg_memory": sum(p.info.memory_percent for p in alive) / max(len(alive), 1),
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            node_id: ps.to_dict()
            for node_id, ps in self._peers.items()
        }
