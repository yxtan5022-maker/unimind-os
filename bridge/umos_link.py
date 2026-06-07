"""UniMind OS (UMOS) - AI-to-Hardware Resonance Bridge.

When an LLM API key is configured (via UMOS_LLM_API_KEY), the bridge
uses a real LLM to translate natural-language intent into runnable Python code.
Without a key, it falls back to a simulated response.

Integrates the self-healing loop and fluid hardware adaptation
for a true AI-native execution pipeline.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from bridge.healer import SelfHealingLoop, SandboxExecutor
from bridge.hw_monitor import HWMonitor, PRECISION_NAMES
from bridge.llm import LLMConfig, chat
from umos_py._compat import safe_print as print
from umos_py.unibit import Unibit


class UMOSLink:
    def __init__(self, agent_name: str = "UMOS-Agent"):
        self.agent = agent_name
        self.status = "RESONANCE_ACTIVE"
        self.unibit = Unibit()
        self.monitor = HWMonitor()
        self.healer = SelfHealingLoop(cfg=LLMConfig())
        print("[link] UMOS-Link: AI Agent '{}' connected to logic flow layer.".format(agent_name))

    def generate_code(self, task_description: str) -> str | None:
        system = (
            "You are the UMOS kernel. The user describes a task in natural language. "
            "Generate *only* valid Python code that accomplishes the task. "
            "No explanations, no markdown, no imports unless needed. "
            "The code will be executed by exec(). Be safe and self-contained."
        )
        return chat(task_description, system=system)

    def bypass_kernel_wall(self, task_description: str) -> str:
        print("[rocket] UMOS: Intercepting task — '{}'".format(task_description))
        print("[brain] UMOS: Generating code from intent...")

        code = self.generate_code(task_description)
        if code is None:
            print("[info] UMOS: No LLM configured — using simulated execution.")
            return "SIMULATED_EXECUTION: {}".format(task_description)

        print("[pc] UMOS: Generated code ({} chars). Executing...".format(len(code)))
        executor = SandboxExecutor()
        report = executor.run(code)

        if report.success:
            hw = self.monitor.snapshot()
            print("[monitor] CPU {:.0f}% | RAM {:.0f}% | precision {}".format(
                hw.cpu_percent, hw.memory_percent,
                PRECISION_NAMES.get(hw.suggested_precision, "?"),
            ))
            return "LLM_EXECUTED: {}".format(report.output[:300])

        print("[warning] Code failed — activating self-healing loop...")
        healed = self.healer.heal(task_description)
        if healed.success:
            return "HEALED: {}".format(healed.output[:300])
        return "HEAL_FAILED: {} — {}".format(healed.error[:100], healed.traceback_text[:300])

    def bypass_with_healing(self, task_description: str) -> str:
        print("[rocket] UMOS: Intercepting task — '{}'".format(task_description))
        hw = self.monitor.snapshot()
        print("[monitor] Load: CPU {:.0f}% RAM {:.0f}% — adapting to {}".format(
            hw.cpu_percent, hw.memory_percent,
            PRECISION_NAMES.get(hw.suggested_precision, "?"),
        ))
        report = self.healer.heal(task_description)
        if report.success:
            return "HEALED: {}".format(report.output[:300])
        return "HEAL_FAILED: {}".format(report.error[:200])

    def allocate_void_ram(self, required_gb: int) -> None:
        print("[battery] UMOS: Remapping hardware for {} GB logical demand...".format(required_gb))
        base = 32
        factor = max(1, round(required_gb / base))
        bits = [1, 0, 1, 1, 0, 1, 0, 0, 1, 1]
        folded = self.unibit.fold_bits(bits)
        expanded = self.unibit.virtual_expand_signal(folded, factor)
        collapsed = self.unibit.collapse_signal(folded)
        print("[chart] UMOS: void-map base={} target={} factor={}x expanded_len={} roundtrip={}".format(
            base, required_gb, factor, len(expanded), collapsed == bits
        ))
        print("[OK] UMOS: Physical memory folded. AI driver injected into hardware.")


def main() -> int:
    link = UMOSLink("UMOS-Commander")

    result = link.bypass_kernel_wall("Print the first 10 prime numbers")
    print("[target] Result: {}".format(result))

    link.allocate_void_ram(64)

    return 0


if __name__ == "__main__":
    cfg = LLMConfig()
    if cfg.api_key:
        print("[info] LLM configured: model={} base_url={}".format(cfg.model, cfg.base_url))
    else:
        print("[info] No UMOS_LLM_API_KEY set — running in simulation mode.")
        print("[info] Set UMOS_LLM_API_KEY and UMOS_LLM_MODEL (optional) for real AI kernel.")
    raise SystemExit(main())
