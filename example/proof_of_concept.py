"""UniMind - Proof of Concept.

Demonstrates the core Unibit pipeline: sliding-window frequency estimation,
sinc folding, and collapse (paper, Sec. 3.2).
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from umos_py._compat import safe_print as print
from umos_py.unibit import Unibit


class UniMindDemonstrator:
    def __init__(self):
        self.version = "0.3.0"
        self.unibit = Unibit()
        print("--- UniMind Unibit Pipeline (PoC v{}) ---".format(self.version))

    def simulate_folding(self, bits):
        print("[Phase 1] Sliding-window frequency estimation + sinc folding on {} bits...".format(len(bits)))
        time.sleep(0.3)
        folded = self.unibit.fold_bits(bits)
        print("[OK] Fold complete. {} folded values.".format(len(folded)))
        return folded

    def simulate_collapse(self, folded):
        print("[Phase 2] Collapsing signal back to binary via threshold...")
        time.sleep(0.3)
        return self.unibit.collapse_signal(folded)


if __name__ == "__main__":
    demo = UniMindDemonstrator()
    data = [1, 0, 1, 1, 0, 1, 0, 0, 1, 1]
    print("Input: {}".format(data))

    folded = demo.simulate_folding(data)
    print("Folded: {}".format([round(x, 4) for x in folded]))

    restored = demo.simulate_collapse(folded)
    print("Restored: {}".format(restored))
