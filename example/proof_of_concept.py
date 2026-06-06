"""UniMind OS (UMOS) - Proof of Concept.

Demonstrates the core Unibit logic folding, collapse, and virtual expansion cycle.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from umos_py._compat import safe_print as print
from umos_py.unibit import Unibit


class UMOS_Demonstrator:
    def __init__(self):
        self.version = "0.2.0"
        self.unibit = Unibit()
        print("--- [UMOS] Logic Morphing Engine (PoC v{}) ---".format(self.version))

    def simulate_logic_folding(self, bits):
        print("[Phase 1] Entropy scanning {} bits...".format(len(bits)))
        time.sleep(0.3)
        folded = self.unibit.fold_bits(bits)
        print("[OK] Logic fold complete. {} folded values.".format(len(folded)))
        return folded

    def simulate_logic_collapse(self, folded):
        print("[Phase 2] Collapsing signal back to binary...")
        time.sleep(0.3)
        return self.unibit.collapse_signal(folded)


if __name__ == "__main__":
    demo = UMOS_Demonstrator()
    data = [1, 0, 1, 1, 0, 1, 0, 0, 1, 1]
    print("Input: {}".format(data))

    folded = demo.simulate_logic_folding(data)
    print("Folded: {}".format([round(x, 4) for x in folded]))

    restored = demo.simulate_logic_collapse(folded)
    print("Restored: {}".format(restored))

    ok = data == restored
    print("[OK] Roundtrip verified: {}\n".format(ok))

    expanded = demo.unibit.virtual_expand_signal(folded, 3)
    print("Virtual expansion (3x): {} values (vs {} input)".format(len(expanded), len(folded)))
