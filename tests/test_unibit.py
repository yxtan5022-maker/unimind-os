"""Tests for the core Unibit engine."""

from __future__ import annotations

import math

from umos_py.unibit import Unibit, UnibitConfig


def test_fold_then_collapse_roundtrip():
    u = Unibit()
    bits = [1, 0, 1, 1, 0, 1, 0, 0, 1, 1]
    folded = u.fold_bits(bits)
    restored = u.collapse_signal(folded)
    assert restored == bits, "roundtrip should preserve input"


def test_fold_length_preserved():
    u = Unibit()
    for length in (1, 2, 8, 16, 64):
        bits = [i % 2 for i in range(length)]
        folded = u.fold_bits(bits)
        assert len(folded) == length


def test_collapse_threshold():
    u = Unibit(UnibitConfig(collapse_threshold=0.9))
    folded = [0.95, 0.1, -0.92, -0.05]
    result = u.collapse_signal(folded)
    assert result == [1, 0, 1, 0]


def test_expand_factor():
    u = Unibit()
    folded = [0.5, 0.3]
    expanded = u.virtual_expand_signal(folded, 3)
    assert len(expanded) == 6


def test_expand_factor_1():
    u = Unibit()
    folded = [0.5, 0.3, 0.1]
    expanded = u.virtual_expand_signal(folded, 1)
    assert len(expanded) == 3


def test_dynamic_weight_uniform():
    u = Unibit()
    bits = [1, 1, 1, 1]
    w0 = u._dynamic_weight(bits, 0)
    assert w0 == 1.0  # zero entropy -> max weight


def test_dynamic_weight_mixed():
    u = Unibit(UnibitConfig(entropy_window=3, weight_floor=0.0))
    bits = [1, 0, 1]
    w = u._dynamic_weight(bits, 1)
    assert 0.0 <= w <= 1.0


def test_as_bits():
    from umos_py.unibit import as_bits
    assert as_bits([1, 0, 1]) == [1, 0, 1]
    assert as_bits([True, False]) == [1, 0]
