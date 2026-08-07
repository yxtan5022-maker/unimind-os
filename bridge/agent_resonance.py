"""UniMind - hardware load monitor wrapper.

Detects real hardware topology (CPU cores, memory) and reports a suggested
AI precision level based on measured system load.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from bridge.hw_monitor import HWMonitor, PRECISION_NAMES, PrecisionLevel
from umos_py._compat import safe_print as print


def _detect_cpu() -> dict:
    try:
        import psutil
        return {
            "cores_physical": psutil.cpu_count(logical=False),
            "cores_logical": psutil.cpu_count(logical=True),
            "memory_gb": round(psutil.virtual_memory().total / (1024**3), 1),
            "memory_available_gb": round(psutil.virtual_memory().available / (1024**3), 1),
        }
    except ImportError:
        cpus = os.cpu_count() or 0
        return {
            "cores_logical": cpus,
            "memory_gb": "unknown (install psutil)",
        }


class ResonanceDriver:
    def __init__(self):
        self.resonance_sync = False
        self.hw = _detect_cpu()
        self.monitor = HWMonitor()
        self.current_precision = PrecisionLevel.FP16
        print("[search] Resonance: Scanning local physical nodes...")

    def activate_sync(self):
        self.resonance_sync = True
        print("[OK] Resonance: Sync established. AI has direct hardware awareness.")
        print("[chart] Topology: {} logical cores, ~{} GB host memory".format(
            self.hw.get("cores_logical", "?"),
            self.hw.get("memory_gb", "?"),
        ))

    def execute_intent(self, intent_vector: str) -> str:
        if not self.resonance_sync:
            return "ERROR: Resonance not established."

        snap = self.monitor.snapshot()
        self.current_precision = snap.suggested_precision

        print("[zap] UMOS: Captured intent vector — '{}'".format(intent_vector))
        print("[info] UMOS: Adapting to {} precision ({}-bit) under {:.0f}% CPU load".format(
            PRECISION_NAMES.get(self.current_precision, "?"),
            self.current_precision,
            snap.cpu_percent,
        ))
        return "SUCCESS: INTENT_MATERIALIZED (via {} cores, {} precision)".format(
            self.hw.get("cores_logical", "?"),
            PRECISION_NAMES.get(self.current_precision, "?"),
        )

    def get_precision(self) -> PrecisionLevel:
        return self.current_precision


def main() -> int:
    driver = ResonanceDriver()
    driver.activate_sync()
    result = driver.execute_intent("RENDER_3D_SCENE_VIA_LOGIC_FLOW")
    print("[target] Result: {}".format(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
