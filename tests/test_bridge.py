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
