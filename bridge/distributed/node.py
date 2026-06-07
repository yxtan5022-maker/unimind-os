"""Distributed UMOS Node — peer discovery, heartbeat, and cluster state.

Uses UDP multicast for LAN discovery and a simple TCP/JSON protocol
for peer-to-peer messaging. No heavy external dependencies.
"""

from __future__ import annotations

import asyncio
import json
import socket
import struct
import sys
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from threading import Lock, Thread
from typing import Any, Callable

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from bridge.distributed.protocol import (
    PeerInfo, ServiceAnnouncement, MessageType, TaskOffer,
)
from bridge.distributed.state import ClusterState, PEER_TIMEOUT_SECONDS
from bridge.hw_monitor import HWMonitor
from umos_py._compat import safe_print as print


MCAST_GROUP = "239.255.77.77"
MCAST_PORT = 7777
LISTEN_PORT = 7778
HEARTBEAT_INTERVAL = 3.0


class NodeStatus(str):
    IDLE = "idle"
    BUSY = "busy"
    OVERLOADED = "overloaded"
    OFFLINE = "offline"


@dataclass
class DistributedNode:
    node_id: str = field(default_factory=lambda: "umos-{}".format(uuid.uuid4().hex[:6]))
    listen_port: int = LISTEN_PORT
    multicast_group: str = MCAST_GROUP
    multicast_port: int = MCAST_PORT
    cluster: ClusterState = field(default_factory=ClusterState)
    _running: bool = False

    def __post_init__(self):
        self.monitor = HWMonitor(enable_cxx_kernel=False)
        self._status = NodeStatus.IDLE
        self._on_message: Callable | None = None
        self._tasks: dict[str, TaskOffer] = {}

    # --- public API ---

    def start(self, on_message: Callable | None = None) -> None:
        self._on_message = on_message
        self._running = True
        t = Thread(target=self._run_io_loop, daemon=True)
        t.start()
        print("[cluster] Node {} started — multicast {}:{}".format(
            self.node_id, self.multicast_group, self.multicast_port
        ))

    def stop(self) -> None:
        self._running = False
        self._broadcast(MessageType.PEER_LEAVE)
        print("[cluster] Node {} stopped".format(self.node_id))

    def offer_task(self, action: str, payload: dict[str, Any],
                   target: str | None = None,
                   priority: int = 0) -> str | None:
        target_node = target
        if target_node is None:
            best = self.cluster.best_target(exclude={self.node_id})
            if best is None:
                print("[cluster] No available peer for task")
                return None
            target_node = best.info.node_id

        offer = TaskOffer(
            source_node=self.node_id,
            target_node=target_node,
            action=action,
            payload=payload,
            priority=priority,
        )
        self._tasks[offer.task_id] = offer
        self._send_to(target_node, {
            "msg_type": MessageType.TASK_OFFER.value,
            "task": offer.to_dict(),
        })
        print("[cluster] Task {} offered to {}".format(offer.task_id[:8], target_node))
        return offer.task_id

    def get_status(self) -> dict[str, Any]:
        snap = self.monitor.snapshot()
        return {
            "node_id": self.node_id,
            "status": self._status,
            "cpu_load": snap.cpu_percent,
            "memory_available_gb": snap.memory_available_gb,
            "memory_percent": snap.memory_percent,
            "precision": snap.to_dict().get("suggested_precision", "fp32"),
            "alive_peers": [p.info.node_id for p in self.cluster.alive_peers],
            "active_tasks": len(self._tasks),
        }

    # --- internal ---

    def _run_io_loop(self) -> None:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self._async_loop())
        finally:
            loop.close()

    async def _async_loop(self) -> None:
        sock = self._create_multicast_socket()

        # listen for unicast messages
        server_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_sock.bind(("0.0.0.0", self.listen_port))
        server_sock.setblocking(False)

        loop = asyncio.get_event_loop()

        # initial broadcast
        self._broadcast(MessageType.PEER_JOIN)

        while self._running:
            # send heartbeat
            self._broadcast(MessageType.HEARTBEAT)

            # read multicast messages
            try:
                data, addr = sock.recvfrom(4096)
                self._handle_message(data, addr)
            except (BlockingIOError, socket.error):
                pass

            # read unicast messages
            try:
                data, addr = server_sock.recvfrom(8192)
                self._handle_message(data, addr)
            except (BlockingIOError, socket.error):
                pass

            await asyncio.sleep(HEARTBEAT_INTERVAL)

        sock.close()
        server_sock.close()

    def _create_multicast_socket(self) -> socket.socket:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(("", self.multicast_port))
        mreq = struct.pack("4sl", socket.inet_aton(self.multicast_group), socket.INADDR_ANY)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
        sock.setblocking(False)
        return sock

    def _own_info(self) -> PeerInfo:
        snap = self.monitor.snapshot()
        host = socket.gethostbyname(socket.gethostname())
        return PeerInfo(
            node_id=self.node_id,
            host=host,
            port=self.listen_port,
            listen_port=self.listen_port,
            cpu_load=snap.cpu_percent,
            memory_available_gb=snap.memory_available_gb,
            memory_percent=snap.memory_percent,
            precision=snap.to_dict().get("suggested_precision", "fp32"),
            available_backends=["classical"],
            last_seen=time.time(),
        )

    def _broadcast(self, msg_type: MessageType) -> None:
        ann = ServiceAnnouncement(
            msg_type=msg_type,
            sender=self._own_info(),
            timestamp=time.time(),
        )
        data = json.dumps(ann.to_dict()).encode()
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
        try:
            sock.sendto(data, (self.multicast_group, self.multicast_port))
        except Exception:
            pass
        finally:
            sock.close()

    def _send_to(self, target_id: str, msg: dict) -> None:
        peer = self.cluster.get(target_id)
        if peer is None:
            return
        data = json.dumps(msg).encode()
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.sendto(data, (peer.info.host, peer.info.listen_port))
            sock.close()
        except Exception:
            pass

    def _handle_message(self, data: bytes, addr: tuple) -> None:
        try:
            msg = json.loads(data.decode())
        except (json.JSONDecodeError, UnicodeDecodeError):
            return

        msg_type = msg.get("msg_type", "heartbeat")
        sender_data = msg.get("sender")
        if sender_data:
            info = PeerInfo.from_dict(sender_data)
            if info.node_id != self.node_id:
                self.cluster.upsert(info)
                if msg_type == MessageType.PEER_LEAVE.value:
                    self.cluster.remove(info.node_id)
                    print("[cluster] Peer {} left".format(info.node_id[:8]))

        if msg_type == MessageType.TASK_OFFER.value:
            task_data = msg.get("task")
            if task_data and self._on_message:
                offer = TaskOffer(
                    task_id=task_data.get("task_id", ""),
                    source_node=task_data.get("source_node", ""),
                    target_node=task_data.get("target_node", ""),
                    action=task_data.get("action", ""),
                    payload=task_data.get("payload", {}),
                    logical_context=task_data.get("logical_context", {}),
                    priority=task_data.get("priority", 0),
                )
                self._on_message(offer)

        if msg_type == MessageType.LOGICAL_MIGRATE.value:
            ctx = msg.get("logical_context", {})
            print("[cluster] Logical migration received: {} keys".format(len(ctx)))


def main() -> int:
    print("[cluster] Starting distributed UMOS node...")
    node = DistributedNode()

    def on_task(offer):
        print("[cluster] Received task: {} — {}".format(offer.action, offer.task_id[:8]))

    node.start(on_message=on_task)
    try:
        for _ in range(10):
            status = node.get_status()
            print("[cluster] Status: CPU={}% RAM={}% peers={}".format(
                status["cpu_load"], status["memory_percent"],
                len(status["alive_peers"]),
            ))
            time.sleep(HEARTBEAT_INTERVAL)
    except KeyboardInterrupt:
        pass
    finally:
        node.stop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
