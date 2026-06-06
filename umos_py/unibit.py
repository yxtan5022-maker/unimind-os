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
    entropy_window: int = 5
    weight_floor: float = 0.85


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

    def virtual_expand_signal(self, folded: Sequence[float], factor: int) -> List[float]:
        factor = max(1, int(factor))
        n = len(folded)
        if n < 2:
            return [float(v) for v in folded]

        out_len = n * factor
        out: List[float] = [0.0] * out_len
        for k in range(out_len):
            t = k / factor
            s = 0.0
            wsum = 0.0
            for i in range(n):
                x = t - i
                if abs(x) < 1e-12:
                    s += folded[i]
                    wsum += 1.0
                elif abs(x) < 6.0:
                    sinc = math.sin(math.pi * x) / (math.pi * x)
                    window = 0.5 * (1.0 + math.cos(math.pi * x / 6.0))
                    weight = sinc * window
                    s += folded[i] * weight
                    wsum += weight
            out[k] = s / wsum if wsum > 0 else 0.0
        return out

    def _py_fold_bits(self, bits: Sequence[int]) -> List[float]:
        out: List[float] = []
        for i, b in enumerate(bits):
            w = self._dynamic_weight(bits, i)
            out.append(math.sin(b * (math.pi / 2.0) + self.cfg.phase_shift) * w)
        return out

    def _dynamic_weight(self, bits: Sequence[int], idx: int) -> float:
        window = max(1, int(self.cfg.entropy_window))
        start = max(0, idx - window // 2)
        end = min(len(bits), idx + window // 2 + 1)
        segment = bits[start:end]
        if not segment:
            return 1.0
        ones = sum(1 for x in segment if x != 0)
        total = len(segment)
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

