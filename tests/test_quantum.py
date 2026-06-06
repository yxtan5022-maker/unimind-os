"""Tests for the quantum module (qiskit stub)."""

from __future__ import annotations

from quantum.qunibit import QUnibit


def test_qunibit_no_qiskit_fallback():
    qu = QUnibit()
    assert qu.available() is False  # no qiskit in CI
    assert qu.fold_bits_circuit([1, 0]) is None
