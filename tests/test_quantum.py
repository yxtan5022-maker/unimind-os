"""Tests for the quantum module (multi-backend)."""

from __future__ import annotations

from collections import Counter

import pytest

from quantum.qunibit import QUnibit, QuantumBackend


def test_qunibit_available_backends():
    qu = QUnibit()
    backends = qu.available_backends()
    assert "classical" in backends
    assert isinstance(backends, list)


def test_qunibit_classical_fold():
    qu = QUnibit()
    bits = [1, 0, 1, 1, 0, 1, 0, 0, 1, 1]
    folded = qu.fold_bits(bits, backend="classical")
    assert folded is not None
    assert len(folded) == len(bits)


def test_qunibit_classical_collapse():
    qu = QUnibit()
    bits = [1, 0, 1, 1, 0, 1, 0, 0, 1, 1]
    folded = qu.fold_bits(bits, backend="classical")
    restored = qu.collapse_signal(folded)
    # The sinc fold (paper Eq. 3) is not a roundtrip-preserving transform:
    # collapse (Eq. 4) merely thresholds the folded signal back to {0,1}.
    assert len(restored) == len(bits)
    assert all(v in (0, 1) for v in restored)


def test_qunibit_set_backend_invalid():
    qu = QUnibit()
    result = qu.set_backend("nonexistent")
    assert result is False


def test_qunibit_backend_enum():
    assert QuantumBackend.CLASSICAL.value == "classical"
    assert QuantumBackend.QISKIT.value == "qiskit"
    assert QuantumBackend.CUDAQ.value == "cudaq"


def test_qunibit_qiskit_fold_gate_counts():
    pytest.importorskip("qiskit")
    pytest.importorskip("qiskit_aer")
    qu = QUnibit()
    bits = [1, 0, 1, 1, 0, 1, 0, 0, 1, 1]
    qc = qu.fold_bits(bits, backend="qiskit")
    assert qc is not None
    counts = Counter(insn.operation.name for insn in qc.data)
    assert counts["x"] == bits.count(1)
    assert counts["ry"] == len(bits)
