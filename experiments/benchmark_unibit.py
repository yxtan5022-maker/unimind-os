"""Experiment B: Performance Micro-Benchmark (Table 4).

Benchmark the sliding-window Unibit computation with *identical* functions on
both sides so the speedup is a rigorous apples-to-apples measurement:

    Table 1 - Frequency estimator (paper Eq. 2):  Pure Python vs NumPy C-backend
    Table 2 - Full Unibit fold (repo engine):     Pure Python vs Rust FFI

System-level strategy:
    1. Rust FFI core (core/target/release/umos_core.dll) is preferred when built.
    2. NumPy's C-optimized vectorized convolution is used as the equivalent
       C-backend proxy for the frequency estimator.

Reference: docs/PAPER_DESIGN.md -> Experiment B (Table 4).
Run: python experiments/benchmark_unibit.py
"""

from __future__ import annotations

import statistics
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

SEQUENCE_LENGTHS = [10_000, 100_000, 1_000_000]
DELTA = 2
RUNS = 3


# --------------------------------------------------------------------------
# Implementations
# --------------------------------------------------------------------------

def unibit_pure_python(bits, delta: int = DELTA):
    """Sliding-window frequency estimation (paper Eq. 2).

    w_i = (1 / |W_i|) * sum_{j in W_i} b_j,  W_i = [i-Delta, i+Delta]
    """
    n = len(bits)
    out = []
    for i in range(n):
        start = max(0, i - delta)
        end = min(n, i + delta + 1)
        seg = bits[start:end]
        out.append(sum(seg) / len(seg))
    return out


def unibit_numpy(bits, delta: int = DELTA):
    """Same frequency estimator via NumPy C-backend (equivalent proxy)."""
    import numpy as np

    arr = np.asarray(bits, dtype=np.float64)
    kernel = np.ones(2 * delta + 1, dtype=np.float64) / (2 * delta + 1)
    return np.convolve(arr, kernel, mode="same").tolist()


def load_rust_engine():
    """Load the repo's Rust FFI engine. Returns (Unibit, rust_available)."""
    from umos_py.unibit import Unibit

    unibit = Unibit()
    return unibit, unibit._lib is not None


# --------------------------------------------------------------------------
# Benchmark harness
# --------------------------------------------------------------------------

def time_impl(fn, data, runs: int = RUNS) -> float:
    fn(data)  # warm-up
    samples = []
    for _ in range(runs):
        t0 = time.perf_counter()
        fn(data)
        t1 = time.perf_counter()
        samples.append((t1 - t0) * 1000.0)
    return statistics.median(samples)


def random_bits(n: int):
    import random

    rng = random.Random(42)
    return [rng.randint(0, 1) for _ in range(n)]


def print_table(title: str, rows: list[tuple[int, float, float]]) -> None:
    print()
    print("### {}".format(title))
    print()
    print("| Sequence Length | Pure Python (ms) | System-Level (ms) | Speedup |")
    print("|---|---:|---:|---:|")
    for n, t_py, t_sys in rows:
        speedup = t_py / t_sys if t_sys > 0 else float("inf")
        print("| {:,} | {:.2f} | {:.2f} | {:.1f}x |".format(n, t_py, t_sys, speedup))
    print()


def main() -> int:
    unibit, rust_available = load_rust_engine()
    if not rust_available:
        try:
            import numpy  # noqa: F401
        except ImportError:
            print("[error] Rust core not built and numpy unavailable - nothing to benchmark.")
            return 1
        print("[info] Rust core not built - using NumPy C-backend proxy only.")

    # --- Table 1: frequency estimator (paper Eq. 2) -----------------------
    rows1 = []
    for n in SEQUENCE_LENGTHS:
        bits = random_bits(n)
        t_py = time_impl(unibit_pure_python, bits)
        t_sys = time_impl(unibit_numpy, bits)
        rows1.append((n, t_py, t_sys))
    print_table("Table 1: Frequency Estimator - Pure Python vs NumPy C-backend", rows1)

    # --- Table 2: full Unibit fold - Pure Python vs Rust FFI ---------------
    if rust_available:
        rows2 = []
        for n in SEQUENCE_LENGTHS:
            bits = random_bits(n)
            t_py = time_impl(unibit._py_fold_bits, bits, runs=min(RUNS, 1 if n >= 1_000_000 else RUNS))
            t_sys = time_impl(unibit.fold_bits, bits)
            rows2.append((n, t_py, t_sys))
        print_table("Table 2: Full Unibit Fold - Pure Python vs Rust FFI", rows2)

    # --- Summary -----------------------------------------------------------
    print("---")
    print("[info] Rust FFI engine loaded: {}".format(rust_available))
    if rust_available:
        print("[info]   library: core/target/release/umos_core.dll")
        print("[info]   Table 2 compares the identical fold function in both implementations.")
    print("[info] Table 1 compares the identical frequency estimator (paper Eq. 2).")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
