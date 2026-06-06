"""Quantum Unibit — maps classical fold/collapse onto quantum circuits.

Requires: pip install umos[quantum]  (qiskit)
"""

from __future__ import annotations

import math
import sys
from dataclasses import dataclass
from typing import Any, List, Sequence


@dataclass
class QUnibitConfig:
    phase_shift: float = 0.42
    collapse_threshold: float = 0.707
    entropy_window: int = 5
    weight_floor: float = 0.85


class QUnibit:
    def __init__(self, cfg: QUnibitConfig | None = None):
        self.cfg = cfg or QUnibitConfig()
        self._qiskit = None
        self._import_qiskit()

    def _import_qiskit(self) -> bool:
        try:
            from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister
            from qiskit_aer import AerSimulator
            self._qiskit = type(sys)("qiskit")
            self._qiskit.QuantumCircuit = QuantumCircuit
            self._qiskit.QuantumRegister = QuantumRegister
            self._qiskit.ClassicalRegister = ClassicalRegister
            self._qiskit.AerSimulator = AerSimulator
            return True
        except ImportError:
            self._qiskit = None
            return False

    def available(self) -> bool:
        return self._qiskit is not None

    def fold_bits_circuit(self, bits: Sequence[int]) -> Any | None:
        if not self.available():
            return None
        qk = self._qiskit
        n = len(bits)
        qr = qk.QuantumRegister(n, "q")
        cr = qk.ClassicalRegister(n, "c")
        qc = qk.QuantumCircuit(qr, cr)

        for i, b in enumerate(bits):
            w = self._dynamic_weight(bits, i)
            theta = 2.0 * math.asin(math.sqrt(w))
            if b == 1:
                qc.x(qr[i])
            qc.ry(theta, qr[i])

        return qc

    def simulate(self, qc: Any) -> List[int] | None:
        if not self.available():
            return None
        qk = self._qiskit
        try:
            qc.measure_all()
            simulator = qk.AerSimulator()
            result = simulator.run(qc, shots=1024).result()
            counts = result.get_counts(qc)
            most_common = max(counts, key=counts.get)
            bits = [int(c) for c in most_common]
            return bits
        except Exception:
            return None

    def _dynamic_weight(self, bits: Sequence[int], idx: int) -> float:
        window = max(1, self.cfg.entropy_window)
        start = max(0, idx - window // 2)
        end = min(len(bits), idx + window // 2 + 1)
        ones = sum(1 for x in bits[start:end] if x != 0)
        total = end - start
        if total == 0:
            return 1.0
        p1 = ones / total
        p0 = 1.0 - p1
        h = 0.0
        if p0 > 0:
            h -= p0 * math.log2(p0)
        if p1 > 0:
            h -= p1 * math.log2(p1)
        ent = max(0.0, min(1.0, h))
        w = self.cfg.weight_floor + (1.0 - self.cfg.weight_floor) * (1.0 - ent)
        return max(self.cfg.weight_floor, min(1.0, w))


def demo() -> None:
    qu = QUnibit()
    if not qu.available():
        print("Qiskit not installed. Run: pip install umos[quantum]")
        return

    bits = [1, 0, 1, 1, 0, 1, 0, 0, 1, 1]
    print("Classical bits: {}".format(bits))

    qc = qu.fold_bits_circuit(bits)
    if qc:
        print("Quantum circuit depth: {}".format(qc.depth()))
        result = qu.simulate(qc)
        print("Measured: {}".format(result))
        print("Match: {}".format(result == bits))


if __name__ == "__main__":
    demo()
