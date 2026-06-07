"""Global Logic Scheduler — load-aware task distribution & logical migration.

The scheduler monitors the cluster, computes each node's logical weight,
and distributes tasks accordingly. When a node is overloaded, its
logical context (JSON state) is migrated to the best available peer.
"""

from __future__ import annotations

import json
import sys
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from bridge.distributed.node import DistributedNode, NodeStatus
from bridge.distributed.protocol import TaskOffer
from bridge.iep.schema import IntentAction, IntentMessage
from bridge.iep.dispatcher import IntentDispatcher
from bridge.hw_monitor import HWMonitor, PrecisionLevel
from umos_py._compat import safe_print as print


class ScheduleStrategy(str, Enum):
    ROUND_ROBIN = "round_robin"
    WEIGHTED = "weighted"
    LEAST_LOADED = "least_loaded"


@dataclass
class ScheduledTask:
    task_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    action: str = ""
    payload: dict[str, Any] = field(default_factory=dict)
    logical_context: dict[str, Any] = field(default_factory=dict)
    source_node: str = ""
    target_node: str = ""
    priority: int = 0
    created_at: float = 0.0
    completed_at: float = 0.0
    success: bool = False


class LogicScheduler:
    def __init__(self, cluster_node: DistributedNode | None = None,
                 strategy: ScheduleStrategy = ScheduleStrategy.WEIGHTED):
        self.cluster = cluster_node
        self.strategy = strategy
        self.dispatcher = IntentDispatcher(cluster_node=cluster_node)
        self.monitor = HWMonitor()
        self._tasks: dict[str, ScheduledTask] = {}
        self._rr_index = 0

    def schedule(self, intent: IntentMessage) -> str | None:
        snap = self.monitor.snapshot()

        # Check if local node is overloaded and should offload
        local_load = max(snap.cpu_percent, snap.memory_percent)

        if local_load >= 75 and self.cluster:
            target = self._pick_target()
            if target and target.info.node_id != self.cluster.node_id:
                return self._offload(intent, target.info.node_id)

        # Execute locally
        return self._execute_local(intent)

    def _pick_target(self) -> Any | None:
        if not self.cluster:
            return None
        alive = self.cluster.cluster.alive_peers

        if self.strategy == ScheduleStrategy.LEAST_LOADED:
            alive.sort(key=lambda p: max(p.info.cpu_load, p.info.memory_percent))
            return alive[0] if alive else None

        if self.strategy == ScheduleStrategy.WEIGHTED:
            alive.sort(key=lambda p: p.logical_weight, reverse=True)
            best = alive[0] if alive else None
            if best and best.logical_weight >= 0.4:
                return best
            return None

        # round-robin
        if not alive:
            return None
        self._rr_index = (self._rr_index + 1) % len(alive)
        return alive[self._rr_index]

    def _offload(self, intent: IntentMessage, target_id: str) -> str | None:
        if not self.cluster:
            return None
        task = ScheduledTask(
            action=intent.action.value,
            payload=intent.payload,
            source_node=self.cluster.node_id,
            target_node=target_id,
            priority=intent.priority,
            created_at=time.time(),
        )
        self._tasks[task.task_id] = task

        snap = self.monitor.snapshot()
        task.logical_context = {
            "source_precision": str(snap.suggested_precision),
            "source_cpu": snap.cpu_percent,
            "source_memory": snap.memory_percent,
            "migrated_at": time.time(),
        }

        tid = self.cluster.offer_task(
            action=task.action,
            payload={
                "task": task.payload.get("task", ""),
                "logical_context": task.logical_context,
            },
            target=target_id,
            priority=task.priority,
        )
        if tid:
            print("[scheduler] Offloaded task {} to {} (load {}%)".format(
                task.task_id[:8], target_id[:8],
                max(snap.cpu_percent, snap.memory_percent),
            ))
            return tid
        return None

    def _execute_local(self, intent: IntentMessage) -> str | None:
        task = ScheduledTask(
            action=intent.action.value,
            payload=intent.payload,
            source_node=self.cluster.node_id if self.cluster else "local",
            target_node=self.cluster.node_id if self.cluster else "local",
            priority=intent.priority,
            created_at=time.time(),
        )
        self._tasks[task.task_id] = task

        resp = self.dispatcher.dispatch(intent)
        task.success = resp.success
        task.completed_at = time.time()

        print("[scheduler] Executed {} locally → {} ({:.0f}ms)".format(
            task.task_id[:8], "OK" if resp.success else "FAIL",
            resp.execution_time_ms,
        ))
        return task.task_id

    def migrate_context(self, ctx: dict[str, Any],
                        target_node: str | None = None) -> bool:
        """Migrate a logical inference context to another node."""
        if not self.cluster:
            return False

        intent = IntentMessage(
            action=IntentAction.MIGRATE,
            payload={"logical_context": ctx},
        )
        tid = self.cluster.offer_task(
            action="migrate",
            payload={"logical_context": ctx},
            target=target_node,
        )
        return tid is not None

    def get_task(self, task_id: str) -> ScheduledTask | None:
        return self._tasks.get(task_id)

    def task_summary(self) -> list[dict[str, Any]]:
        return [
            {
                "task_id": t.task_id,
                "action": t.action,
                "source": t.source_node[:8],
                "target": t.target_node[:8],
                "success": t.success,
                "duration_ms": round(
                    (t.completed_at - t.created_at) * 1000
                ) if t.completed_at > 0 else None,
            }
            for t in self._tasks.values()
        ]


def main() -> int:
    print("[scheduler] Logic Scheduler demo")

    scheduler = LogicScheduler()

    # Simulate a few tasks
    tasks = [
        IntentMessage(action=IntentAction.COMPUTE,
                       payload={"task": "result = sum(i*i for i in range(100))"}),
        IntentMessage(action=IntentAction.FOLD,
                       payload={"bits": [1, 0, 1, 1, 0, 1, 0, 0, 1, 1]}),
        IntentMessage(action=IntentAction.QUERY_STATUS),
    ]

    for intent in tasks:
        scheduler.schedule(intent)
        time.sleep(0.1)

    print("\n[scheduler] Task summary:")
    for t in scheduler.task_summary():
        print("  {} → {} ({})".format(t["task_id"][:8], t["action"], t["success"]))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
