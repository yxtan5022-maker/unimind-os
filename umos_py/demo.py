from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from .unibit import Unibit


def _try_run_topo_mapper() -> None:
    repo_root = Path(__file__).resolve().parent.parent
    candidates = [
        repo_root / "build" / "kernel" / "umos_topo_mapper",
        repo_root / "build" / "kernel" / "umos_topo_mapper.exe",
        repo_root / "build" / "umos_topo_mapper",
        repo_root / "build" / "umos_topo_mapper.exe",
    ]
    for p in candidates:
        if p.exists():
            subprocess.run([str(p)], check=False)
            return


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="umos-demo")
    parser.add_argument("--bits", default="1011010011")
    parser.add_argument("--expand", type=int, default=2)
    parser.add_argument("--run-topo-mapper", action="store_true")
    args = parser.parse_args(argv)

    bits = [1 if c == "1" else 0 for c in str(args.bits).strip()]
    u = Unibit()

    folded = u.fold_bits(bits)
    collapsed = u.collapse_signal(folded)
    expanded = u.virtual_expand_signal(folded, args.expand)

    print("--- UMOS Phase1 Demo ---")
    print("bits:", bits)
    print("folded:", [round(x, 4) for x in folded])
    print("collapsed:", collapsed)
    print("expanded_len:", len(expanded))
    print("roundtrip_ok:", collapsed == bits)

    if args.run_topo_mapper:
        _try_run_topo_mapper()

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

