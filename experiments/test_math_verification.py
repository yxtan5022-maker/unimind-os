"""Experiment A: Mathematical Verification of Unibit Angle Encoding (Table 3).

For target Unibit weights w in {0.1, 0.3, 0.5, 0.7, 0.9}, prepare the single-qubit
state |psi_i> via the angle-encoding mapping

    theta_i = 2 * arcsin(sqrt(w_i))          (paper Eq. angle mapping)

and simulate 8192 projective measurements on the ideal Qiskit AerSimulator.

Verification observable (paper Eq. <Z>):
    <Z>_theory = 1 - 2*w_i
    <Z>_emp    = 1 - 2*P(1)_emp

Reference: docs/PAPER_DESIGN.md -> Experiment A (Table 3).
Run directly:
    python experiments/test_math_verification.py
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister
from qiskit_aer import AerSimulator


TARGET_WEIGHTS = [0.1, 0.3, 0.5, 0.7, 0.9]
SHOTS = 8192
SEED = 42  # fixed AerSimulator seed -> reproducible results
MAX_DEV = 0.05  # asserted tolerance: |<Z>_emp - <Z>_theory| < 0.05


def rotation_angle(w: float) -> float:
    """theta_i = 2 * arcsin(sqrt(w_i))."""
    return 2.0 * math.asin(math.sqrt(w))


def build_circuit(theta: float) -> QuantumCircuit:
    """Single-qubit angle-encoded circuit: Ry(theta) -> Measure."""
    qr = QuantumRegister(1, "q")
    cr = ClassicalRegister(1, "c")
    qc = QuantumCircuit(qr, cr)
    qc.ry(theta, qr[0])
    qc.measure(qr[0], cr[0])
    return qc


def run_experiment(shots: int = SHOTS, seed: int = SEED) -> list[dict[str, float]]:
    simulator = AerSimulator()
    rows: list[dict[str, float]] = []
    for w in TARGET_WEIGHTS:
        theta = rotation_angle(w)
        circuit = build_circuit(theta)
        result = simulator.run(circuit, shots=shots, seed_simulator=seed).result()
        counts = result.get_counts(circuit)
        p1 = counts.get("1", 0) / shots
        rows.append(
            {
                "w": w,
                "p1": p1,
                "z_theory": 1.0 - 2.0 * w,
                "z_emp": 1.0 - 2.0 * p1,
                "dev": abs((1.0 - 2.0 * p1) - (1.0 - 2.0 * w)),
            }
        )
    return rows


def print_table(rows: list[dict[str, float]]) -> None:
    print()
    print("Mathematical Verification via {}-Shot AerSimulator Measurement".format(SHOTS))
    print("-" * 74)
    print(
        "{:>8} | {:>10} | {:>12} | {:>12} | {:>10}".format(
            "Target w", "P(1) emp", "<Z> theory", "<Z> emp", "|dev|"
        )
    )
    print("-" * 74)
    for r in rows:
        print(
            "{:>8.4f} | {:>10.6f} | {:>12.6f} | {:>12.6f} | {:>10.6f}".format(
                r["w"], r["p1"], r["z_theory"], r["z_emp"], r["dev"]
            )
        )
    print("-" * 74)
    max_dev = max(r["dev"] for r in rows)
    print("Max absolute deviation  |<Z>_emp - <Z>_theory| = {:.6f}".format(max_dev))
    print("Tolerance < 0.05: {}\n".format("PASS" if max_dev < MAX_DEV else "FAIL"))


def assert_verification(rows: list[dict[str, float]]) -> None:
    max_dev = max(r["dev"] for r in rows)
    assert max_dev < MAX_DEV, (
        "Mathematical verification failed: max deviation {:.6f} >= {}".format(
            max_dev, MAX_DEV
        )
    )


def main() -> int:
    rows = run_experiment()
    print_table(rows)
    assert_verification(rows)
    print("[OK] All {} target weights satisfy |<Z>_emp - <Z>_theory| < 0.05".format(len(rows)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
