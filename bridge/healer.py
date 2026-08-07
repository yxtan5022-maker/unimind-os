"""Self-Healing Mechanism for UniMind.

Captures run-time errors from LLM-generated code and feeds the
traceback back to the AI for automatic correction in a closed
monitor-feedback loop.

Generated code is executed within a *restricted namespace* (paper, Sec. 4.4):
a static analysis rejects obvious dangerous patterns and only a safe subset
of builtins is exposed. Full OS-level sandboxing is intentionally not
implemented (paper, Sec. 6, T4).
"""

from __future__ import annotations

import builtins
import io
import sys
import traceback
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from bridge.llm import LLMConfig, chat
from umos_py._compat import safe_print as print


_SAFE_BUILTIN_NAMES = (
    "abs", "all", "any", "bin", "bool", "bytearray", "bytes", "chr", "complex",
    "dict", "divmod", "enumerate", "filter", "float", "format", "frozenset",
    "hash", "hex", "int", "isinstance", "issubclass", "len", "list", "map",
    "max", "min", "oct", "ord", "pow", "print", "range", "repr", "reversed",
    "round", "set", "slice", "sorted", "str", "sum", "tuple", "zip",
    "Exception", "ValueError", "TypeError", "NameError", "ImportError",
    "ArithmeticError", "OverflowError", "ZeroDivisionError",
)
_SAFE_BUILTINS = {
    name: getattr(builtins, name)
    for name in _SAFE_BUILTIN_NAMES
    if hasattr(builtins, name)
}

_BLOCKED_PATTERNS = (
    "open(", "eval(", "exec(", "compile(", "getattr(", "setattr(",
    "__import__", "os.", "subprocess", "shutil", "pickle",
)


def static_analysis(code: str) -> str | None:
    """Return the first blocked pattern found, or None if the code is clean."""
    for pat in _BLOCKED_PATTERNS:
        if pat in code:
            return pat
    return None


@dataclass
class ExecutionReport:
    code: str
    success: bool
    output: str
    error: str
    traceback_text: str


class SandboxExecutor:
    def __init__(self, timeout_seconds: int = 10):
        self.timeout = timeout_seconds

    def run(self, code: str) -> ExecutionReport:
        risk = static_analysis(code)
        if risk is not None:
            return ExecutionReport(
                code=code,
                success=False,
                output="",
                error="static analysis rejected: '{}'".format(risk),
                traceback_text="",
            )

        stdout_buf = io.StringIO()
        stderr_buf = io.StringIO()
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        sys.stdout = stdout_buf
        sys.stderr = stderr_buf

        try:
            local_ns: dict[str, Any] = {}
            exec(code, {"__builtins__": _SAFE_BUILTINS}, local_ns)
            result = local_ns.get("result", local_ns.get("output", "EXECUTED_OK"))
            return ExecutionReport(
                code=code,
                success=True,
                output="stdout: {}\nresult: {}".format(stdout_buf.getvalue().strip(), str(result)[:500]),
                error="",
                traceback_text="",
            )
        except Exception:
            tb = traceback.format_exc()
            return ExecutionReport(
                code=code,
                success=False,
                output=stdout_buf.getvalue().strip(),
                error=str(sys.exc_info()[1]),
                traceback_text=tb,
            )
        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr


class SelfHealingLoop:
    def __init__(self, max_retries: int = 3, cfg: LLMConfig | None = None):
        self.max_retries = max_retries
        self.cfg = cfg or LLMConfig()
        self.executor = SandboxExecutor()
        self.history: list[dict] = []

    def heal(self, task: str, max_retries: int | None = None) -> ExecutionReport:
        max_r = max_retries if max_retries is not None else self.max_retries

        system = (
            "You are the UniMind self-healing orchestrator (user space). Generate *only* valid Python code "
            "for the given task. The code will be executed via exec(). "
            "Assign the final result to a variable named 'result' or 'output'. "
            "Do NOT use markdown, explanations, or imports unless required by the task. "
            "Be safe and self-contained."
        )

        code = self._generate(task, system)
        if code is None:
            return ExecutionReport(
                code="", success=False, output="", error="LLM unavailable",
                traceback_text="",
            )

        for attempt in range(max_r + 1):
            print("[heal] Attempt {}/{} — executing {} chars of code".format(
                attempt + 1, max_r + 1, len(code)
            ))
            report = self.executor.run(code)
            self.history.append({
                "attempt": attempt, "task": task, "code": code, "report": report,
            })

            if report.success:
                print("[heal] Execution SUCCEEDED on attempt {}".format(attempt + 1))
                return report

            print("[heal] Execution FAILED: {}".format(report.error[:120]))
            if attempt >= max_r:
                print("[heal] Max retries reached — giving up.")
                return report

            fix_prompt = (
                "The following Python code failed with an error.\n\n"
                "--- CODE ---\n{}\n\n--- TRACEBACK ---\n{}\n\n"
                "Fix the code so it runs without errors. "
                "Return *only* the corrected Python code. "
                "Assign the result to 'result' or 'output'."
            ).format(code, report.traceback_text)

            code = self._generate(fix_prompt)
            if code is None:
                return report

        return report

    def _generate(self, prompt: str, system: str = "") -> str | None:
        raw = chat(prompt, system=system, cfg=self.cfg)
        if raw is None:
            return None
        return self._strip_code_fences(raw)

    @staticmethod
    def _strip_code_fences(text: str) -> str:
        lines = text.strip().splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        return "\n".join(lines).strip()


def main() -> int:
    cfg = LLMConfig()
    if not cfg.api_key:
        print("[info] Set UMOS_LLM_API_KEY for real self-healing. Running demo instead.")

    healer = SelfHealingLoop(max_retries=2, cfg=cfg)
    report = healer.heal("Compute the 20th Fibonacci number and store it in 'result'. Print it.")

    print("\n=== FINAL REPORT ===")
    print("Success: {}".format(report.success))
    print("Output: {}".format(report.output[:300]))
    if not report.success:
        print("Error: {}".format(report.error))
    return 0 if report.success else 1


if __name__ == "__main__":
    raise SystemExit(main())
