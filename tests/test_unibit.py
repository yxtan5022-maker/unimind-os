"""Tests for the core Unibit engine (paper, Sec. 3.2, Eqs. 2-4)."""

from __future__ import annotations

import math

from umos_py.unibit import Unibit, UnibitConfig


def test_fold_length_preserved():
    u = Unibit()
    for length in (1, 2, 8, 16, 64):
        bits = [i % 2 for i in range(length)]
        folded = u.fold_bits(bits)
        assert len(folded) == length


def test_fold_all_zeros_is_zero():
    u = Unibit()
    bits = [0, 0, 0, 0, 0]
    assert all(s == 0.0 for s in u.fold_bits(bits))


def test_fold_matches_paper_equation():
    u = Unibit()
    n = 5
    bits = [1, 1, 1, 1, 1]
    folded = u.fold_bits(bits)
    # All-ones -> every window frequency w_i = 1, so s_i = sinc((i+phi)*pi/n).
    for i in range(n):
        x = (i + u.cfg.phase_shift) * math.pi / n
        expected = math.sin(x) / x
        assert abs(folded[i] - expected) < 1e-12


def test_sliding_window_frequency():
    from umos_py.unibit import Unibit as U
    # bits = [1,0,1,1,0], delta=2. At index 0 the window is [0,2]=[1,0,1] -> 2/3.
    bits = [1, 0, 1, 1, 0]
    w0 = U.sliding_window_weight(bits, 0, 2)
    assert abs(w0 - 2.0 / 3.0) < 1e-12
    # At index 1 the window is [0,3]=[1,0,1,1] -> 3/4.
    w1 = U.sliding_window_weight(bits, 1, 2)
    assert abs(w1 - 3.0 / 4.0) < 1e-12


def test_collapse_threshold():
    u = Unibit(UnibitConfig(collapse_threshold=0.9))
    folded = [0.95, 0.1, -0.92, -0.05]
    result = u.collapse_signal(folded)
    assert result == [1, 0, 1, 0]


def test_collapse_default_threshold():
    u = Unibit()
    folded = [0.8, 0.6, -0.8, -0.6]
    assert u.collapse_signal(folded) == [1, 0, 1, 0]


def test_as_bits():
    from umos_py.unibit import as_bits
    assert as_bits([1, 0, 1]) == [1, 0, 1]
    assert as_bits([True, False]) == [1, 0]
