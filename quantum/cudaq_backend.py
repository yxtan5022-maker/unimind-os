"""NVIDIA CUDA-Q backend for UMOS — hybrid quantum-classical acceleration.

Provides CUDA-Q kernel definitions for the Unibit folding/collapse
workflow, plus a pluggable backend that can target either a GPU
simulator or a real QPU (IonQ, Quantinuum, etc.).

Requirements (Linux x86_64 + NVIDIA GPU recommended):
    pip install cudaq

On Windows or without a GPU, this module degrades gracefully and
falls back to a descriptive stub.
"""

from __future__ import annotations

import math
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, List, Sequence

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from umos_py._compat import safe_print as print


CUDAQ_AVAILABLE = False
CUDAQ_IMPORT_ERROR: str | None = None

try:
    import cudaq

    CUDAQ_AVAILABLE = True
except ImportError as e:
    CUDAQ_AVAILABLE = False
    CUDAQ_IMPORT_ERROR = str(e)


CUDAQ_SUPPORTED_BACKENDS: list[str] = []

if CUDAQ_AVAILABLE:
    try:
        CUDAQ_SUPPORTED_BACKENDS = [
            t.name for t in cudaq.list_targets()
        ]
    except Exception:
        CUDAQ_SUPPORTED_BACKENDS = []


def is_available() -> bool:
    return CUDAQ_AVAILABLE


def available_backends() -> list[str]:
    return list(CUDAQ_SUPPORTED_BACKENDS)


@dataclass
class CUDAQConfig:
    backend: str = ""
    shots: int = 1024
    target: str = ""


class CUDAQBackend:
    def __init__(self, cfg: CUDAQConfig | None = None):
        self.cfg = cfg or CUDAQConfig()
        self._initialized = False

        if not CUDAQ_AVAILABLE:
            print("[cudaq] CUDA-Q not installed — backend unavailable")
            return

        if self.cfg.target and self.cfg.target in CUDAQ_SUPPORTED_BACKENDS:
            try:
                cudaq.set_target(self.cfg.target)
                print("[cudaq] Target set to '{}'".format(self.cfg.target))
            except Exception as e:
                print("[cudaq] Failed to set target '{}': {}".format(
                    self.cfg.target, e
                ))

        self._initialized = True
        print("[cudaq] CUDA-Q backend ready (targets: {})".format(
            ", ".join(CUDAQ_SUPPORTED_BACKENDS[:5])
        ))

    def sample(self, kernel_fn: Any, *args: Any, **kwargs: Any) -> dict[str, int] | None:
        if not self._initialized:
            return None
        try:
            shots = kwargs.pop("shots", self.cfg.shots)
            counts = cudaq.sample(kernel_fn, *args, shots_count=shots, **kwargs)
            return {str(k): int(v) for k, v in counts.items()}
        except Exception as e:
            print("[cudaq] Sample failed: {}".format(e))
            return None

    def observe(self, kernel_fn: Any, hamiltonian: Any,
                 *args: Any, **kwargs: Any) -> float | None:
        if not self._initialized:
            return None
        try:
            result = cudaq.observe(kernel_fn, hamiltonian, *args, **kwargs)
            return float(result.expectation())
        except Exception as e:
            print("[cudaq] Observe failed: {}".format(e))
            return None

    def get_state(self, kernel_fn: Any, *args: Any) -> Any | None:
        if not self._initialized:
            return None
        try:
            return cudaq.get_state(kernel_fn, *args)
        except Exception as e:
            print("[cudaq] get_state failed: {}".format(e))
            return None


if CUDAQ_AVAILABLE:

    @cudaq.kernel
    def _fold_kernel(bits: List[int], phase: float):
        qvec = cudaq.qvector(len(bits))
        for i in range(len(bits)):
            theta = math.asin(math.sqrt(0.5 + 0.5 * bits[i]))
            if bits[i]:
                x(qvec[i])
            ry(2.0 * theta + phase, qvec[i])
        mz(qvec)

    @cudaq.kernel
    def _ghz_kernel(n: int):
        qvec = cudaq.qvector(n)
        h(qvec[0])
        for i in range(n - 1):
            cx(qvec[i], qvec[i + 1])
        mz(qvec)

    def make_fold_kernel(bits: Sequence[int], phase: float = 0.42):
        return _fold_kernel, list(bits), phase

    def make_ghz_kernel(n: int):
        return _ghz_kernel, n

else:

    def make_fold_kernel(bits: Sequence[int], phase: float = 0.42):
        return None

    def make_ghz_kernel(n: int):
        return None


def demo() -> None:
    if not CUDAQ_AVAILABLE:
        print("[cudaq] CUDA-Q not installed.")
        print("[cudaq] On Linux with an NVIDIA GPU: pip install cudaq")
        return

    bits = [1, 0, 1, 1, 0, 1, 0, 0, 1, 1]
    print("[cudaq] Classical bits: {}".format(bits))

    backend = CUDAQBackend()
    kernel_fn, args = make_fold_kernel(bits)
    counts = backend.sample(kernel_fn, *args)
    if counts:
        print("[cudaq] Sample counts: {}".format(counts))

    ghz_fn, n = make_ghz_kernel(4)
    ghz_counts = backend.sample(ghz_fn, n)
    if ghz_counts:
        print("[cudaq] GHZ-4 counts: {}".format(ghz_counts))


if __name__ == "__main__":
    demo()
