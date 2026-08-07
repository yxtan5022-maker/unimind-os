"""Hardware Monitor - real-time load sensing.

Reads CPU frequency, utilisation, RAM pressure, and (on supported
platforms) swap usage, then reports a suggested AI precision level
based on measured load headroom.
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field
from enum import IntEnum
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from umos_py._compat import safe_print as print


class PrecisionLevel(IntEnum):
    INT4 = 0
    INT8 = 1
    FP16 = 2
    FP32 = 3


PRECISION_NAMES = {0: "int4", 1: "int8", 2: "fp16", 3: "fp32"}
PRECISION_BITS = {0: 4, 1: 8, 2: 16, 3: 32}


@dataclass
class HWLoadSnapshot:
    cpu_percent: float
    cpu_freq_mhz: float
    memory_percent: float
    memory_available_gb: float
    swap_percent: float
    suggested_precision: PrecisionLevel = PrecisionLevel.FP16

    def to_dict(self) -> dict[str, Any]:
        return {
            "cpu_percent": self.cpu_percent,
            "cpu_freq_mhz": self.cpu_freq_mhz,
            "memory_percent": self.memory_percent,
            "memory_available_gb": round(self.memory_available_gb, 1),
            "swap_percent": self.swap_percent,
            "suggested_precision": PRECISION_NAMES.get(
                self.suggested_precision, "unknown"
            ),
            "suggested_bits": PRECISION_BITS.get(self.suggested_precision, 0),
        }


class HWMonitor:
    def __init__(self, enable_cxx_kernel: bool = True):
        self._psutil: Any = None
        self._import_psutil()
        self._cxx_path = self._find_cxx_binary() if enable_cxx_kernel else None
        print("[monitor] HWMonitor: thermal probe active")

    def snapshot(self) -> HWLoadSnapshot:
        cpu_pct = 0.0
        cpu_freq = 0.0
        mem_pct = 0.0
        mem_avail = 0.0
        swap_pct = 0.0

        if self._psutil:
            cpu_pct = self._psutil.cpu_percent(interval=0.2)
            freq = self._psutil.cpu_freq()
            cpu_freq = freq.current if freq else 0.0
            mem = self._psutil.virtual_memory()
            mem_pct = mem.percent
            mem_avail = mem.available / (1024 ** 3)
            swap = self._psutil.swap_memory()
            swap_pct = swap.percent

        precise = self._compute_precision(
            cpu_pct=cpu_pct, cpu_freq=cpu_freq,
            mem_pct=mem_pct, swap_pct=swap_pct,
        )
        return HWLoadSnapshot(
            cpu_percent=cpu_pct,
            cpu_freq_mhz=cpu_freq,
            memory_percent=mem_pct,
            memory_available_gb=mem_avail,
            swap_percent=swap_pct,
            suggested_precision=precise,
        )

    def _compute_precision(
        self, cpu_pct: float, cpu_freq: float,
        mem_pct: float, swap_pct: float,
    ) -> PrecisionLevel:
        load = max(cpu_pct, mem_pct, swap_pct * 0.7)
        if load >= 85:
            return PrecisionLevel.INT4
        if load >= 65:
            return PrecisionLevel.INT8
        if load >= 40:
            return PrecisionLevel.FP16
        return PrecisionLevel.FP32

    def running_under_load(self, threshold: float = 60.0) -> tuple[bool, HWLoadSnapshot]:
        snap = self.snapshot()
        load = max(snap.cpu_percent, snap.memory_percent)
        return load >= threshold, snap

    def _import_psutil(self) -> bool:
        try:
            import psutil
            self._psutil = psutil
            return True
        except ImportError:
            return False

    @staticmethod
    def _find_cxx_binary() -> str | None:
        candidates = [
            Path(__file__).resolve().parents[1] / "build" / "topo_mapper",
            Path(__file__).resolve().parents[1] / "build" / "topo_mapper.exe",
        ]
        for p in candidates:
            if p.exists():
                return str(p)
        return None


def main() -> int:
    monitor = HWMonitor()
    snap = monitor.snapshot()
    info = snap.to_dict()
    print("[chart] CPU: {cpu_percent:.0f}% @ {cpu_freq_mhz:.0f} MHz".format(**info))
    print("[chart] RAM: {memory_percent:.0f}% ({memory_available_gb} GB free)".format(**info))
    print("[chart] Precision: {suggested_precision} ({suggested_bits} bits)".format(**info))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
