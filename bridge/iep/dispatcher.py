"""Intent Dispatcher — the "brain concierge".

Receives an IEP intent from any Agent, queries the topology mapper for
available resources, and routes the task to the correct backend.
"""

from __future__ import annotations

import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from bridge.distributed.node import DistributedNode
from bridge.healer import SandboxExecutor, _SAFE_BUILTINS, static_analysis
from bridge.hw_monitor import HWMonitor, PRECISION_NAMES
from bridge.iep.schema import (
    IntentAction, IntentMessage, IntentResponse, ResourceCapability,
)
from bridge.llm import LLMConfig, chat
from umos_py._compat import safe_print as print
from umos_py.unibit import Unibit, UnibitConfig


@dataclass
class IntentResult:
    success: bool
    message: str
    result: Any = None
    target_node: str = ""
    execution_time_ms: float = 0.0


class IntentDispatcher:
    def __init__(self, cluster_node: DistributedNode | None = None):
        self.cluster = cluster_node
        self.monitor = HWMonitor(enable_cxx_kernel=False)
        self.unibit = Unibit()
        self.executor = SandboxExecutor()
        self._capabilities = self._detect_capabilities()

    def dispatch(self, intent: IntentMessage) -> IntentResponse:
        t0 = time.time()

        if intent.action == IntentAction.QUERY_STATUS:
            return self._handle_query_status(t0)

        if intent.action == IntentAction.QUERY_TOPOLOGY:
            return self._handle_query_topology(t0)

        if intent.action == IntentAction.FOLD:
            return self._handle_fold(intent, t0)

        if intent.action == IntentAction.COLLAPSE:
            return self._handle_collapse(intent, t0)

        if intent.action == IntentAction.EXPAND:
            return self._handle_expand(intent, t0)

        if intent.action == IntentAction.COMPUTE:
            return self._handle_compute(intent, t0)

        if intent.action == IntentAction.HEAL:
            return self._handle_heal(intent, t0)

        if intent.action == IntentAction.MIGRATE:
            return self._handle_migrate(intent, t0)

        if intent.action == IntentAction.CUSTOM:
            return self._handle_custom(intent, t0)

        elapsed = (time.time() - t0) * 1000
        return IntentResponse(
            success=False,
            message="Unknown action: {}".format(intent.action),
            execution_time_ms=elapsed,
        )

    def _detect_capabilities(self) -> ResourceCapability:
        cap = ResourceCapability()
        try:
            from quantum.cudaq_backend import is_available as cudaq_avail
            cap.has_cudaq = cudaq_avail()
        except ImportError:
            cap.has_cudaq = False
        try:
            from quantum.qunibit import QUnibit
            qu = QUnibit()
            backends = qu.available_backends()
            cap.has_quantum = "qiskit" in backends or "cudaq" in backends
        except ImportError:
            cap.has_quantum = False
        snap = self.monitor.snapshot()
        cap.precision = snap.to_dict().get("suggested_precision", "fp32")
        return cap

    def _handle_query_status(self, t0: float) -> IntentResponse:
        snap = self.monitor.snapshot()
        status = {
            "cpu_percent": snap.cpu_percent,
            "memory_percent": snap.memory_percent,
            "precision": PRECISION_NAMES.get(snap.suggested_precision, "?"),
            "capabilities": self._capabilities.to_dict(),
        }
        if self.cluster:
            status["cluster"] = self.cluster.cluster.cluster_summary()
        elapsed = (time.time() - t0) * 1000
        return IntentResponse(
            success=True, message="Node status",
            result=status, execution_time_ms=elapsed,
        )

    def _handle_query_topology(self, t0: float) -> IntentResponse:
        from bridge.agent_resonance import ResonanceDriver
        driver = ResonanceDriver()
        elapsed = (time.time() - t0) * 1000
        return IntentResponse(
            success=True, message="Topology",
            result=driver.hw, execution_time_ms=elapsed,
        )

    def _handle_fold(self, intent: IntentMessage, t0: float) -> IntentResponse:
        bits = intent.payload.get("bits", [1, 0, 1, 1])
        try:
            folded = self.unibit.fold_bits(bits)
            elapsed = (time.time() - t0) * 1000
            return IntentResponse(
                success=True, message="Bits folded",
                result=[round(v, 4) for v in folded],
                execution_time_ms=elapsed,
            )
        except Exception as e:
            elapsed = (time.time() - t0) * 1000
            return IntentResponse(
                success=False, message=str(e), execution_time_ms=elapsed,
            )

    def _handle_collapse(self, intent: IntentMessage, t0: float) -> IntentResponse:
        folded = intent.payload.get("folded", [])
        threshold = intent.payload.get("threshold")
        try:
            restored = self.unibit.collapse_signal(folded, threshold)
            elapsed = (time.time() - t0) * 1000
            return IntentResponse(
                success=True, message="Signal collapsed",
                result=restored, execution_time_ms=elapsed,
            )
        except Exception as e:
            elapsed = (time.time() - t0) * 1000
            return IntentResponse(
                success=False, message=str(e), execution_time_ms=elapsed,
            )

    def _handle_expand(self, intent: IntentMessage, t0: float) -> IntentResponse:
        folded = intent.payload.get("folded", [])
        factor = intent.payload.get("factor", 2)
        elapsed = (time.time() - t0) * 1000
        # Signal upsampling is not part of the paper's Unibit pipeline
        # (Eqs. 2-4); the action is acknowledged but not executed.
        return IntentResponse(
            success=False,
            message="EXPAND not supported: not part of the paper's Unibit definition",
            result={"folded_len": len(folded), "factor": factor},
            execution_time_ms=elapsed,
        )

    def _handle_compute(self, intent: IntentMessage, t0: float) -> IntentResponse:
        task = intent.payload.get("task", "result = 42")

        # try to offload to a cluster peer
        if self.cluster:
            best = self.cluster.cluster.best_target(exclude={self.cluster.node_id})
            if best and best.logical_weight > 0.3:
                tid = self.cluster.offer_task("compute", {"task": task},
                                               target=best.info.node_id)
                if tid:
                    elapsed = (time.time() - t0) * 1000
                    return IntentResponse(
                        success=True, message="Offloaded to {}".format(best.info.node_id[:8]),
                        result={"task_id": tid, "target": best.info.node_id},
                        target_node=best.info.node_id,
                        execution_time_ms=elapsed,
                    )

        # local execution with self-healing
        try:
            risk = static_analysis(task)
            if risk is not None:
                raise RuntimeError("static analysis rejected: '{}'".format(risk))
            ns: dict = {}
            exec(task, {"__builtins__": _SAFE_BUILTINS}, ns)
            result = ns.get("result", ns.get("output", "OK"))
            elapsed = (time.time() - t0) * 1000
            return IntentResponse(
                success=True, message="Computed locally",
                result=str(result)[:300],
                execution_time_ms=elapsed,
            )
        except Exception as e:
            # self-heal
            from bridge.healer import SelfHealingLoop
            healer = SelfHealingLoop(max_retries=2)
            report = healer.heal(task)
            elapsed = (time.time() - t0) * 1000
            if report.success:
                return IntentResponse(
                    success=True, message="Computed after healing",
                    result=report.output[:300],
                    execution_time_ms=elapsed,
                )
            return IntentResponse(
                success=False, message="Compute failed: {}".format(report.error),
                execution_time_ms=elapsed,
            )

    def _handle_heal(self, intent: IntentMessage, t0: float) -> IntentResponse:
        task = intent.payload.get("task", "")
        from bridge.healer import SelfHealingLoop
        healer = SelfHealingLoop(max_retries=3)
        report = healer.heal(task)
        elapsed = (time.time() - t0) * 1000
        return IntentResponse(
            success=report.success,
            message="Healed" if report.success else "Heal failed",
            result=report.output[:400] if report.success else report.error,
            execution_time_ms=elapsed,
        )

    def _handle_migrate(self, intent: IntentMessage, t0: float) -> IntentResponse:
        ctx = intent.payload.get("logical_context", {})
        if not ctx:
            elapsed = (time.time() - t0) * 1000
            return IntentResponse(
                success=False, message="Empty logical context",
                execution_time_ms=elapsed,
            )
        # In a full implementation, this restores the AI inference context
        print("[iep] Logical migration: received {} keys".format(len(ctx)))
        elapsed = (time.time() - t0) * 1000
        return IntentResponse(
            success=True, message="Context migrated ({} keys)".format(len(ctx)),
            result={"keys": list(ctx.keys())[:10]},
            execution_time_ms=elapsed,
        )

    def _handle_custom(self, intent: IntentMessage, t0: float) -> IntentResponse:
        payload = intent.payload
        action_name = intent.action.value

        llm = LLMConfig()
        if llm.api_key:
            prompt = (
                "You are the UMOS Intent Dispatcher. "
                "A custom action '{}' was requested with payload: {}\n"
                "Generate Python code to handle this action. "
                "Assign result to 'result'."
            ).format(action_name, str(payload)[:500])
            code = chat(prompt, system="", cfg=llm)
            if code:
                ns: dict = {}
                try:
                    risk = static_analysis(code)
                    if risk is not None:
                        raise RuntimeError("static analysis rejected: '{}'".format(risk))
                    exec(code, {"__builtins__": _SAFE_BUILTINS}, ns)
                    result = ns.get("result", "CUSTOM_EXECUTED")
                    elapsed = (time.time() - t0) * 1000
                    return IntentResponse(
                        success=True, message="Custom action handled by LLM",
                        result=str(result)[:300],
                        execution_time_ms=elapsed,
                    )
                except Exception as e:
                    elapsed = (time.time() - t0) * 1000
                    return IntentResponse(
                        success=False, message=str(e),
                        execution_time_ms=elapsed,
                    )

        elapsed = (time.time() - t0) * 1000
        return IntentResponse(
            success=True, message="Custom action acknowledged (no LLM)",
            result="CUSTOM:{}".format(action_name),
            execution_time_ms=elapsed,
        )


def main() -> int:
    print("[iep] Intent Dispatcher demo")

    dispatcher = IntentDispatcher()

    # Test queries
    for action in (IntentAction.QUERY_STATUS, IntentAction.FOLD):
        intent = IntentMessage(action=action)
        resp = dispatcher.dispatch(intent)
        print("[iep] {} → success={} time={}ms".format(
            action.value, resp.success, resp.execution_time_ms
        ))
        if resp.result:
            print("[iep]   result: {}".format(str(resp.result)[:120]))

    # Test fold with payload
    intent = IntentMessage(
        action=IntentAction.FOLD,
        payload={"bits": [1, 0, 1, 1, 0, 1, 0, 0, 1, 1]},
    )
    resp = dispatcher.dispatch(intent)
    print("[iep] fold → success={} result={}".format(resp.success, str(resp.result)[:80]))

    # Test compute
    intent = IntentMessage(
        action=IntentAction.COMPUTE,
        payload={"task": "result = sum(range(100))"},
    )
    resp = dispatcher.dispatch(intent)
    print("[iep] compute → success={} result={}".format(resp.success, resp.result))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
