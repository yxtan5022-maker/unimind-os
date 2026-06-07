"""Smoke tests for bridge modules."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def test_detect_host_arch():
    from bridge.cross_arch_vm import detect_host_arch
    info = detect_host_arch()
    assert "arch" in info
    assert "bits" in info
    assert "system" in info
    assert info["bits"] in (32, 64)


def test_resonance_driver_no_crash():
    from bridge.agent_resonance import ResonanceDriver
    d = ResonanceDriver()
    d.activate_sync()
    r = d.execute_intent("TEST_VECTOR")
    assert "SUCCESS" in r


def test_umos_link_no_crash():
    from bridge.umos_link import UMOSLink
    link = UMOSLink("test-agent")
    r = link.bypass_kernel_wall("test task")
    # Without LLM configured, should fall back to simulation
    assert r.startswith("SIMULATED") or r.startswith("LLM_")


def test_universal_vm_no_crash():
    from bridge.cross_arch_vm import UniversalVM
    vm = UniversalVM()
    r = vm.bridge_app("test-app", "test-os")
    assert "CROSS_ARCH_OK" in r


def test_sandbox_executor_success():
    from bridge.healer import SandboxExecutor
    exe = SandboxExecutor()
    r = exe.run("result = 2 + 2")
    assert r.success
    assert "4" in r.output or "4" in r.error


def test_sandbox_executor_failure():
    from bridge.healer import SandboxExecutor
    exe = SandboxExecutor()
    r = exe.run("raise ValueError('boom')")
    assert not r.success
    assert "boom" in r.error or "ValueError" in r.traceback_text


def test_sandbox_executor_traceback():
    from bridge.healer import SandboxExecutor
    exe = SandboxExecutor()
    r = exe.run("undefined_var + 1")
    assert not r.success
    assert "NameError" in r.traceback_text


def test_self_healing_strip_fences():
    from bridge.healer import SelfHealingLoop
    assert SelfHealingLoop._strip_code_fences("```python\nx = 1\n```") == "x = 1"
    assert SelfHealingLoop._strip_code_fences("```\nx = 1\n```") == "x = 1"
    assert SelfHealingLoop._strip_code_fences("x = 1") == "x = 1"


def test_hw_monitor_load_snapshot():
    from bridge.hw_monitor import HWMonitor
    mon = HWMonitor(enable_cxx_kernel=False)
    snap = mon.snapshot()
    assert snap.cpu_percent >= 0.0
    assert snap.memory_percent >= 0.0


def test_hw_monitor_precision_levels():
    from bridge.hw_monitor import HWMonitor, PrecisionLevel
    mon = HWMonitor(enable_cxx_kernel=False)
    snap = mon.snapshot()
    assert isinstance(snap.suggested_precision, PrecisionLevel)


def test_resonance_driver_fluid_precision():
    from bridge.agent_resonance import ResonanceDriver
    d = ResonanceDriver()
    d.activate_sync()
    r = d.execute_intent("TEST_VECTOR")
    assert "SUCCESS" in r
    assert "precision" in r


def test_peer_info_roundtrip():
    from bridge.distributed.protocol import PeerInfo
    p = PeerInfo(node_id="n1", host="127.0.0.1", port=7777)
    d = p.to_dict()
    p2 = PeerInfo.from_dict(d)
    assert p2.node_id == "n1"
    assert p2.host == "127.0.0.1"


def test_service_announcement_roundtrip():
    from bridge.distributed.protocol import PeerInfo, ServiceAnnouncement
    p = PeerInfo(node_id="n1", host="127.0.0.1", port=7777)
    a = ServiceAnnouncement(sender=p)
    d = a.to_dict()
    a2 = ServiceAnnouncement.from_dict(d)
    assert a2.msg_type == a.msg_type


def test_intent_message_roundtrip():
    from bridge.iep.schema import IntentMessage, IntentAction
    m = IntentMessage(action=IntentAction.COMPUTE, payload={"task": "test"})
    d = m.to_dict()
    m2 = IntentMessage.from_dict(d)
    assert m2.action == IntentAction.COMPUTE
    assert m2.payload["task"] == "test"


def test_cluster_state_upsert():
    from bridge.distributed.state import ClusterState
    from bridge.distributed.protocol import PeerInfo
    cs = ClusterState()
    p = PeerInfo(node_id="n1", host="127.0.0.1", port=7777)
    cs.upsert(p)
    assert cs.get("n1") is not None
    assert cs.get("n1").info.node_id == "n1"


def test_cluster_state_best_target():
    from bridge.distributed.state import ClusterState
    from bridge.distributed.protocol import PeerInfo
    cs = ClusterState()
    p1 = PeerInfo(node_id="n1", host="127.0.0.1", port=7777, cpu_load=10, memory_percent=20)
    cs.upsert(p1)
    best = cs.best_target(exclude={"nonexistent"})
    assert best is not None
    assert best.info.node_id == "n1"


def test_intent_dispatcher_fold():
    from bridge.iep.schema import IntentMessage, IntentAction
    from bridge.iep.dispatcher import IntentDispatcher
    disp = IntentDispatcher()
    intent = IntentMessage(action=IntentAction.FOLD, payload={"bits": [1, 0, 1]})
    resp = disp.dispatch(intent)
    assert resp.success
    assert len(resp.result) == 3


def test_intent_dispatcher_compute():
    from bridge.iep.schema import IntentMessage, IntentAction
    from bridge.iep.dispatcher import IntentDispatcher
    disp = IntentDispatcher()
    intent = IntentMessage(action=IntentAction.COMPUTE, payload={"task": "result = 2 + 2"})
    resp = disp.dispatch(intent)
    assert resp.success
    assert "4" in str(resp.result)


def test_logic_scheduler_local():
    from bridge.scheduler import LogicScheduler
    from bridge.iep.schema import IntentMessage, IntentAction
    sched = LogicScheduler()
    intent = IntentMessage(action=IntentAction.QUERY_STATUS)
    tid = sched.schedule(intent)
    assert tid is not None


def test_distributed_node_clean_start_stop():
    from bridge.distributed.node import DistributedNode
    node = DistributedNode()
    node.start()
    import time
    time.sleep(0.5)
    status = node.get_status()
    assert "node_id" in status
    assert "cpu_load" in status
    node.stop()
