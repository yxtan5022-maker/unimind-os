#!/usr/bin/env python3
"""UniMind OS (UMOS) - Quick-launch entry point."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

if __name__ == "__main__":
    from umos_py.demo import main
    raise SystemExit(main(sys.argv[1:]))
