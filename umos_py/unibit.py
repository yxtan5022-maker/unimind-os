from __future__ import annotations

import ctypes
import math
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional, Sequence


@dataclass(frozen=True)
class UnibitConfig:
    phase_shift: float = 0.42
    collapse_threshold: float = 0.707
    window_delta: int = 2


class Unibit:
    def __init__(self, cfg: UnibitConfig | None = None, rust_lib_path: str | os.PathLike | None = None):
        self.cfg = cfg or UnibitConfig()
        self._lib = self._try_load_rust_lib(rust_lib_path)

    def fold_bits(self, bits: Sequence[int]) -> List[float]:
        normalized = [0 if int(b) == 0 else 1 for b in bits]
        if self._lib is None:
            return self._py_fold_bits(normalized)
        return self._rust_fold_bits(normalized)

    def collapse_signal(self, folded: Sequence[float], threshold: Optional[float] = None) -> List[int]:
        thr = float(self.cfg.collapse_threshold if threshold is None else threshold)
        if self._lib is None:
            return [1 if abs(float(s)) > thr else 0 for s in folded]
        return self._rust_collapse_signal([float(x) for x in folded], thr)

    @staticmethod
    def sliding_window_weight(bits: Sequence[int], idx: int, delta: int) -> float:
        """Paper Eq. 2: w_i = (1 / |W_i|) * sum_{j in W_i} b_j, W_i = [i-delta, i+delta]."""
        start = max(0, idx - delta)
        end = min(len(bits), idx + delta + 1)
        window = bits[start:end]
        return float(sum(window)) / float(len(window)) if window else 0.0

    def _py_fold_bits(self, bits: Sequence[int]) -> List[float]:
        """Paper Eqs. 2-3: sliding-window frequency + sinc folding.

        s_i = w_i * sinc((i + phi) * pi / n),  sinc(x) = sin(x)/x.
        """
        n = len(bits)
        if n == 0:
            return []
        out: List[float] = []
        for i, _b in enumerate(bits):
            w = self.sliding_window_weight(bits, i, self.cfg.window_delta)
            x = (i + self.cfg.phase_shift) * math.pi / n
            s = math.sin(x) / x if abs(x) > 1e-12 else 1.0
            out.append(w * s)
        return out

    def _try_load_rust_lib(self, rust_lib_path: str | os.PathLike | None) -> Optional[ctypes.CDLL]:
        candidates: List[Path] = []

        if rust_lib_path:
            candidates.append(Path(rust_lib_path))

        repo_root = Path(__file__).resolve().parent.parent
        for profile in ("release", "debug"):
            candidates.append(repo_root / "core" / "target" / profile / "umos_core.dll")
            candidates.append(repo_root / "core" / "target" / profile / "libumos_core.so")
            candidates.append(repo_root / "core" / "target" / profile / "libumos_core.dylib")

        for p in candidates:
            if p.exists():
                lib = ctypes.CDLL(str(p))
                self._configure_ffi(lib)
                return lib
        return None

    def _configure_ffi(self, lib: ctypes.CDLL) -> None:
        lib.umos_fold_bits.argtypes = [ctypes.POINTER(ctypes.c_uint8), ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)]
        lib.umos_fold_bits.restype = ctypes.POINTER(ctypes.c_double)

        lib.umos_collapse_signal.argtypes = [
            ctypes.POINTER(ctypes.c_double),
            ctypes.c_size_t,
            ctypes.c_double,
            ctypes.POINTER(ctypes.c_size_t),
        ]
        lib.umos_collapse_signal.restype = ctypes.POINTER(ctypes.c_uint8)

        lib.umos_free_f64.argtypes = [ctypes.POINTER(ctypes.c_double), ctypes.c_size_t]
        lib.umos_free_f64.restype = None

        lib.umos_free_u8.argtypes = [ctypes.POINTER(ctypes.c_uint8), ctypes.c_size_t]
        lib.umos_free_u8.restype = None

    def _rust_fold_bits(self, bits: Sequence[int]) -> List[float]:
        assert self._lib is not None

        n = len(bits)
        buf = (ctypes.c_uint8 * n)(*bits)
        out_len = ctypes.c_size_t(0)
        ptr = self._lib.umos_fold_bits(buf, n, ctypes.byref(out_len))
        if not ptr:
            raise RuntimeError("umos_fold_bits returned NULL")
        try:
            out = [ptr[i] for i in range(out_len.value)]
            return [float(x) for x in out]
        finally:
            self._lib.umos_free_f64(ptr, out_len.value)

    def _rust_collapse_signal(self, signal: Sequence[float], threshold: float) -> List[int]:
        assert self._lib is not None

        n = len(signal)
        buf = (ctypes.c_double * n)(*signal)
        out_len = ctypes.c_size_t(0)
        ptr = self._lib.umos_collapse_signal(buf, n, float(threshold), ctypes.byref(out_len))
        if not ptr:
            raise RuntimeError("umos_collapse_signal returned NULL")
        try:
            out = [ptr[i] for i in range(out_len.value)]
            return [int(x) for x in out]
        finally:
            self._lib.umos_free_u8(ptr, out_len.value)


def as_bits(values: Iterable[int]) -> List[int]:
    return [0 if int(v) == 0 else 1 for v in values]

