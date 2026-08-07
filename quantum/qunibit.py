"""Quantum Unibit — multi-backend quantum folding engine.

Backends
--------
- "classical" : Always available. Python-based sinc interpolation.
- "qiskit"    : Requires `pip install umos[quantum]` (qiskit).
- "cudaq"     : Requires `pip install cudaq` (Linux + NVIDIA GPU recommended).
"""

from __future__ import annotations

import math
import sys
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, List, Sequence

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from umos_py._compat import safe_print as print


class QuantumBackend(str, Enum):
    CLASSICAL = "classical"
    QISKIT = "qiskit"
    CUDAQ = "cudaq"


BACKEND_NAMES = {b.value: b for b in QuantumBackend}


@dataclass
class QUnibitConfig:
    phase_shift: float = 0.42
    collapse_threshold: float = 0.707
    entropy_window: int = 5
    weight_floor: float = 0.85
    backend: str = "classical"
    cudaq_target: str = ""
    qiskit_shots: int = 1024
    cudaq_shots: int = 1024


class QUnibit:
    def __init__(self, cfg: QUnibitConfig | None = None):
        self.cfg = cfg or QUnibitConfig()
        self._qiskit: Any = None
        self._cudaq_backend: Any = None
        self._classical: Any = None

        self._init_classical()
        self._init_qiskit()
        self._init_cudaq()

    # --- public API ---

    def fold_bits(self, bits: Sequence[int], backend: str | None = None) -> Any | None:
        b = (backend or self.cfg.backend)
        if b == QuantumBackend.QISKIT:
            return self._fold_qiskit(bits)
        if b == QuantumBackend.CUDAQ:
            return self._fold_cudaq(bits)
        return self._fold_classical(bits)

    def collapse_signal(self, folded: Sequence[float],
                        threshold: float | None = None) -> List[int] | None:
        thr = float(self.cfg.collapse_threshold if threshold is None else threshold)
        return [1 if abs(float(s)) > thr else 0 for s in folded]

    def simulate(self, backend: str | None = None,
                 **kwargs: Any) -> List[int] | dict | None:
        b = (backend or self.cfg.backend)
        if b == QuantumBackend.QISKIT:
            return self._simulate_qiskit(**kwargs)
        if b == QuantumBackend.CUDAQ:
            return self._simulate_cudaq(**kwargs)
        return None

    def available_backends(self) -> list[str]:
        backends = ["classical"]
        if self._qiskit:
            backends.append("qiskit")
        if self._cudaq_backend and self._cudaq_backend._initialized:
            backends.append("cudaq")
        return backends

    def set_backend(self, backend: str) -> bool:
        if backend not in self.available_backends():
            print("[qunibit] Backend '{}' not available. Choices: {}".format(
                backend, self.available_backends()
            ))
            return False
        self.cfg.backend = backend
        print("[qunibit] Switched to '{}' backend".format(backend))
        return True

    # --- classical ---

    def _init_classical(self):
        from umos_py.unibit import Unibit, UnibitConfig
        self._classical = Unibit(
            UnibitConfig(
                phase_shift=self.cfg.phase_shift,
                collapse_threshold=self.cfg.collapse_threshold,
                entropy_window=self.cfg.entropy_window,
                weight_floor=self.cfg.weight_floor,
            )
        )

    def _fold_classical(self, bits: Sequence[int]) -> List[float] | None:
        return self._classical.fold_bits(bits) if self._classical else None

    # --- qiskit ---

    def _init_qiskit(self) -> bool:
        try:
            from qiskit import (ClassicalRegister, QuantumCircuit,
                                QuantumRegister)
            from qiskit_aer import AerSimulator
            self._qiskit = type(sys)("qiskit_stub")
            self._qiskit.QuantumCircuit = QuantumCircuit
            self._qiskit.QuantumRegister = QuantumRegister
            self._qiskit.ClassicalRegister = ClassicalRegister
            self._qiskit.AerSimulator = AerSimulator
            return True
        except ImportError:
            self._qiskit = None
            return False

    def _fold_qiskit(self, bits: Sequence[int]) -> Any | None:
        if not self._qiskit:
            return None
        qk = self._qiskit
        n = len(bits)
        qr = qk.QuantumRegister(n, "q")
        cr = qk.ClassicalRegister(n, "c")
        qc = qk.QuantumCircuit(qr, cr)

        for i, b in enumerate(bits):
            w = self._classical._dynamic_weight(bits, i)
            # Angle-encoding mapping (paper, Sec. 4.3). The Ry gate acts as
            #   Ry(theta)|0> = cos(theta/2)|0> + sin(theta/2)|1>,
            # so the |1>-state probability is sin^2(theta/2). Choosing
            #   theta_i = 2 * arcsin(sqrt(w_i))
            # yields sin^2(theta_i/2) = w_i, i.e. the measured |1> probability
            # matches the Unibit sliding-window weight exactly. arcsin (not
            # arccos) is used so w=0 -> theta=0 (no rotation) and w=1 -> theta=pi
            # (full rotation), an intuitive monotonic correspondence.
            theta = 2.0 * math.asin(math.sqrt(w))
            if b == 1:
                qc.x(qr[i])
            qc.ry(theta, qr[i])

        return qc

    def _simulate_qiskit(self, **kwargs: Any) -> List[int] | None:
        if not self._qiskit:
            return None
        qk = self._qiskit
        qc = kwargs.get("circuit")
        if qc is None:
            return None
        shots = kwargs.get("shots", self.cfg.qiskit_shots)
        try:
            qc.measure_all()
            simulator = qk.AerSimulator()
            result = simulator.run(qc, shots=shots).result()
            counts = result.get_counts(qc)
            most_common = max(counts, key=counts.get)
            return [int(c) for c in most_common]
        except Exception as e:
            print("[qunibit] Qiskit simulation failed: {}".format(e))
            return None

    # --- cudaq ---

    def _init_cudaq(self) -> bool:
        try:
            from quantum.cudaq_backend import CUDAQBackend, CUDAQConfig
            self._cudaq_backend = CUDAQBackend(
                CUDAQConfig(
                    target=self.cfg.cudaq_target,
                    shots=self.cfg.cudaq_shots,
                )
            )
            return self._cudaq_backend._initialized
        except Exception:
            self._cudaq_backend = None
            return False

    def _fold_cudaq(self, bits: Sequence[int]) -> Any | None:
        if not self._cudaq_backend or not self._cudaq_backend._initialized:
            return None
        try:
            from quantum.cudaq_backend import make_fold_kernel
            return make_fold_kernel(bits, self.cfg.phase_shift)
        except Exception:
            return None

    def _simulate_cudaq(self, **kwargs: Any) -> dict[str, int] | None:
        if not self._cudaq_backend or not self._cudaq_backend._initialized:
            return None
        from quantum.cudaq_backend import make_fold_kernel
        kernel_data = kwargs.get("kernel_data")
        if kernel_data is None:
            return None
        kernel_fn, *args = kernel_data
        return self._cudaq_backend.sample(kernel_fn, *args, **kwargs)


def demo() -> None:
    qu = QUnibit()
    print("[qunibit] Available backends: {}".format(qu.available_backends()))

    bits = [1, 0, 1, 1, 0, 1, 0, 0, 1, 1]
    print("[qunibit] Bits: {}".format(bits))

    classical = qu.fold_bits(bits, backend="classical")
    print("[qunibit] Classical fold: {}...".format(
        [round(v, 3) for v in classical[:5]] if classical else "N/A"
    ))

    if "qiskit" in qu.available_backends():
        print("[qunibit] Qiskit available — switching to quantum simulation")
        qc = qu.fold_bits(bits, backend="qiskit")
        if qc:
            result = qu.simulate(backend="qiskit", circuit=qc)
            print("[qunibit] Qiskit simulation result: {}".format(result))

    if "cudaq" in qu.available_backends():
        print("[qunibit] CUDA-Q available — switching to GPU/QPU backend")
        kernel_data = qu.fold_bits(bits, backend="cudaq")
        if kernel_data:
            result = qu.simulate(backend="cudaq", kernel_data=kernel_data)
            print("[qunibit] CUDA-Q result: {}".format(result))


if __name__ == "__main__":
    demo()
