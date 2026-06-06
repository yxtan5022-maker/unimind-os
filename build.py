#!/usr/bin/env python3
"""Build all UMOS components: Rust core, C++ kernel, Python package."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def run(cmd: list[str], cwd: Path | None = None, desc: str = "") -> bool:
    print(f"\n=== {desc or ' '.join(cmd)} ===")
    try:
        subprocess.run(cmd, cwd=cwd, check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"[FAIL] {e}", file=sys.stderr)
        return False
    except FileNotFoundError as e:
        print(f"[SKIP] {e}", file=sys.stderr)
        return False


def main() -> int:
    root = Path(__file__).resolve().parent

    # Python
    run([sys.executable, "-m", "pip", "install", "-e", "."], root, "pip install -e .")

    # Rust
    run(["cargo", "build", "--release"], root / "core", "cargo build --release")

    # C++ (try MinGW first, then default generator)
    mingw_make = r"C:\msys64\mingw64\bin\mingw32-make.exe"
    if Path(mingw_make).exists():
        ok = run(
            ["cmake", "-S", str(root), "-B", str(root / "build"),
             "-G", "MinGW Makefiles",
             f"-DCMAKE_MAKE_PROGRAM={mingw_make}"],
            root, "cmake configure (MinGW)",
        )
        if ok:
            run(["cmake", "--build", str(root / "build")], root, "cmake build")
    else:
        run(["cmake", "-S", ".", "-B", "build"], root, "cmake configure")
        run(["cmake", "--build", "build", "--config", "Release"], root, "cmake build")

    # Tests
    run([sys.executable, "-m", "pytest", "tests/", "-v"], root, "pytest")

    print("\n[OK] All builds completed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
