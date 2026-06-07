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
