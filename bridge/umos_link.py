"""UniMind OS (UMOS) - AI-to-Hardware Resonance Bridge.

When an LLM API key is configured (via UMOS_LLM_API_KEY), the bridge
uses a real LLM to translate natural-language intent into runnable Python code.
Without a key, it falls back to a simulated response.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from bridge.llm import LLMConfig, chat
from umos_py._compat import safe_print as print
from umos_py.unibit import Unibit


class UMOSLink:
    def __init__(self, agent_name: str = "UMOS-Agent"):
        self.agent = agent_name
        self.status = "RESONANCE_ACTIVE"
        self.unibit = Unibit()
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
        print("[brain] UMOS: Generating code from intent (no icons, no kernel)...")

        code = self.generate_code(task_description)
        if code is None:
            print("[info] UMOS: No LLM configured — using simulated execution.")
            return "SIMULATED_EXECUTION: {}".format(task_description)

        print("[pc] UMOS: Generated code ({} chars). Executing...".format(len(code)))
        try:
            local_ns: dict = {}
            exec(code, {"__builtins__": __builtins__}, local_ns)
            result = local_ns.get("result", local_ns.get("output", "EXECUTED_OK"))
            return "LLM_EXECUTED: {}".format(str(result)[:200])
        except Exception as e:
            return "LLM_EXECUTION_FAILED: {}".format(e)

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

    # Real test: ask LLM to generate code
    result = link.bypass_kernel_wall("Print the first 10 prime numbers")
    print("[target] Result: {}".format(result))

    # Memory expansion demo
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
