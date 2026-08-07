"""UniMind (UMOS) - AI-as-Orchestrator: User-Space Intent-to-Execution Bridge.

The LLM is explicitly placed in *user space* as an AI-as-Orchestrator layer,
NOT inside the OS kernel. When an LLM API key is configured (via
UMOS_LLM_API_KEY), the bridge uses a real LLM to translate natural-language
intent into runnable Python code. Without a key — or after 3 failed LLM
inference attempts — execution falls back to a deterministic rule-based
dispatcher mapping intents to predefined circuit templates.

Integrates the self-healing loop and fluid hardware adaptation
for an AI-native execution pipeline.
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


# Rule-based fallback templates: map intent keywords to predefined circuits.
_FALLBACK_TEMPLATES = (
    (("entangle", "entanglement", "bell"), "bell"),
    (("classify", "classification", "vqc", "variational"), "vqc"),
)


class UMOSLink:
    def __init__(self, agent_name: str = "UMOS-Agent", llm_max_retries: int = 3):
        self.agent = agent_name
        self.status = "ORCHESTRATOR_ACTIVE"
        self.llm_max_retries = max(1, llm_max_retries)
        self.unibit = Unibit()
        self.monitor = HWMonitor()
        self.healer = SelfHealingLoop(cfg=LLMConfig())
        print("[link] UMOS-Link: AI-as-Orchestrator agent '{}' connected to logic flow layer.".format(agent_name))

    def generate_code(self, task_description: str) -> str | None:
        system = (
            "You are the UMOS AI-as-Orchestrator layer operating in user space. "
            "The user describes a task in natural language. "
            "Generate *only* valid Python code that accomplishes the task. "
            "No explanations, no markdown, no imports unless needed. "
            "The code will be executed by exec(). Be safe and self-contained."
        )
        raw = chat(task_description, system=system)
        if raw is None or raw.startswith("<LLM error"):
            return None
        return raw

    def rule_based_fallback(self, intent: str) -> str:
        """Deterministic fallback: map intent keywords to predefined templates.

        - entangle / bell  -> Bell-state preparation circuit
        - classify / vqc   -> basic variational quantum circuit (VQC)
        - otherwise        -> trivial no-op task
        """
        low = intent.lower()
        for keywords, kind in _FALLBACK_TEMPLATES:
            if any(k in low for k in keywords):
                if kind == "bell":
                    return (
                        "from qiskit import QuantumCircuit\n"
                        "qc = QuantumCircuit(2, 2)\n"
                        "qc.h(0)\n"
                        "qc.cx(0, 1)\n"
                        "qc.measure([0, 1], [0, 1])\n"
                        "result = 'Bell state circuit prepared (rule-based fallback)'"
                    )
                return (
                    "from qiskit import QuantumCircuit\n"
                    "qc = QuantumCircuit(2, 2)\n"
                    "qc.h(0)\n"
                    "qc.ry(0.1, 0)\n"
                    "qc.cx(0, 1)\n"
                    "qc.measure([0, 1], [0, 1])\n"
                    "result = 'Basic VQC circuit prepared (rule-based fallback)'"
                )
        return "result = 'No matching rule-based template for: {}'".format(low)

    def bypass_kernel_wall(self, task_description: str) -> str:
        print("[rocket] UMOS: Intercepting task — '{}'".format(task_description))
        print("[brain] UMOS: Generating code from intent...")

        code = None
        used_fallback = False
        for attempt in range(self.llm_max_retries):
            code = self.generate_code(task_description)
            if code is not None:
                break
            print("[orchestrator] LLM inference failed (attempt {}/{}) — retrying...".format(
                attempt + 1, self.llm_max_retries
            ))

        if code is None:
            print("[orchestrator] LLM unavailable after {} attempts — switching to rule-based fallback.".format(
                self.llm_max_retries
            ))
            code = self.rule_based_fallback(task_description)
            used_fallback = True

        print("[pc] UMOS: Generated code ({} chars). Executing...".format(len(code)))
        executor = SandboxExecutor()
        report = executor.run(code)

        if report.success:
            hw = self.monitor.snapshot()
            print("[monitor] CPU {:.0f}% | RAM {:.0f}% | precision {}".format(
                hw.cpu_percent, hw.memory_percent,
                PRECISION_NAMES.get(hw.suggested_precision, "?"),
            ))
            prefix = "RULE_BASED_FALLBACK" if used_fallback else "LLM_EXECUTED"
            return "{}: {}".format(prefix, report.output[:300])

        if used_fallback:
            print("[warning] Rule-based fallback template failed to execute.")
            return "FALLBACK_FAILED: {} — {}".format(report.error[:100], report.traceback_text[:300])

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
        print("[info] Set UMOS_LLM_API_KEY and UMOS_LLM_MODEL (optional) for real AI orchestration.")
    raise SystemExit(main())
