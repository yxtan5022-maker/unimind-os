# UniMind Framework Design Spec (Based on Peer-Reviewed Paper)

## 1. Architecture Renaming
- "AI-as-Kernel" MUST be renamed to "AI-as-Orchestrator". It operates in user space, not kernel space.
- Add a "Rule-based Fallback" mechanism to the Orchestrator. If LLM fails 3 times, fallback to predefined circuit templates (e.g., Bell state, Variational Ansatz).

## 2. Unibit Definition Update
- Unibit is a "sliding-window frequency estimation" (NOT entropy).
- Sinc folding is used as an "anti-aliasing / band-limited smoothing kernel".
- Angle encoding mapping: theta_i = 2 * arcsin(sqrt(w_i)).
- Mathematical verification observable: <Z>_i = 1 - 2*w_i.

## 3. Required Experiments (Must be implemented and tested locally)
### Experiment A: Mathematical Verification (Table 3)
- Target weights: [0.1, 0.3, 0.5, 0.7, 0.9]
- Use Qiskit AerSimulator with 8192 shots.
- Measure P(1) and calculate empirical <Z>.
- Assert that max absolute deviation between empirical <Z> and theoretical (1 - 2w) is < 0.05.

### Experiment B: Performance Micro-Benchmark (Table 4)
- Benchmark Pure Python sliding-window vs Rust FFI (or Numpy C-backend proxy).
- Test sequence lengths: 10_000, 100_000, 1_000_000.
- Output a formatted table showing Speedup (expecting 20x - 40x).
