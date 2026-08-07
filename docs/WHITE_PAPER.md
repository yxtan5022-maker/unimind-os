# UniMind Technical Whitepaper

English | [简体中文](WHITE_PAPER.zh-CN.md)

UniMind is a **user-space quantum-classical middleware research prototype**. It pairs a classical preprocessing representation (Unibit) with an LLM-driven orchestrator that plans task execution; there is no fabricated "operating system", no virtual-memory expansion, and no kernel bypass. This document describes what the code actually implements, the mathematics behind it, and the measured evidence.

## 1. Unibit: Classical Preprocessing for Quantum Angle Encoding

Unibit maps a binary sequence into rotation parameters for standard single-qubit angle encoding. The transform has three steps, all implemented identically in Python and in the Rust FFI engine.

**Step 1 — Sliding-window frequency (paper Eq. 2).** Each bit is replaced by the local frequency of 1-bits over a centered window of half-width `window_delta`:

$$w_i = \frac{1}{|W_i|} \sum_{j \in W_i} b_j$$

**Step 2 — Sinc smoothing (paper Eq. 3).** The weighted signal is multiplied by a sinc envelope scaled by the sequence length `n` and a fixed phase shift `phi`:

$$s_i = w_i \cdot \operatorname{sinc}\!\left(\frac{(i+\phi)\,\pi}{n}\right)$$

**Step 3 — Collapse (paper Eq. 4).** The smoothed signal is thresholded back to discrete values by `collapse_threshold tau`:

$$\text{collapse}(s_i) = \begin{cases} 1 & |s_i| > \tau \\ 0 & \text{otherwise} \end{cases}$$

A single-qubit state is then prepared per parameter with rotation angle `theta = 2*arcsin(sqrt(w_i))`, which sets the measurement probability of the excited state to `w_i`.

## 2. Quantum Mapping

The mapping engine (Qiskit) builds a multi-qubit circuit with `n` parameterized `R_y(theta)` gates, one per classical bit, plus optional measurement. Simulation uses an ideal AerSimulator; the accompanying experiment verifies that empirical measurement frequencies converge to the theoretical weights within binomial sampling variance.

## 3. LLM-Driven Orchestration (User Space)

The orchestrator interprets natural-language task specifications, plans execution, and dispatches the plan to local executor tools. It operates **exclusively in user space**:

- LLM output is validated in a restricted-namespace sandbox (`SandboxExecutor`) that whitelists safe builtins and rejects risky patterns (`open(`, `eval(`, `exec(`, `os.`, `subprocess`) via static analysis before any execution.
- When the LLM is unavailable or the generated plan fails, a rule-based fallback executes simple intent actions (fold, compute, status).
- Unsupported intent actions return an honest "not supported" response rather than fabricating results.

## 4. Hardware Detection

`kernel/topo_mapper.cpp` is a C++17 program that detects the host's logical/physical core count, OS, architecture, and total RAM, and emits the result as JSON on stdout. It performs no "adaptive performance" logic; it is a hardware probe consumed by the orchestrator.

## 5. Measured Evidence

### Experiment A — Mathematical verification (Qiskit AerSimulator, 8192 shots, fixed seed)

| Target w | P(1) empirical | <Z> theory | <Z> empirical | dev |
|---:|---:|---:|---:|---:|
| 0.1 | 0.095459 | 0.800000 | 0.809082 | 0.009082 |
| 0.3 | 0.296875 | 0.400000 | 0.406250 | 0.006250 |
| 0.5 | 0.505493 | 0.000000 | -0.010986 | 0.010986 |
| 0.7 | 0.704590 | -0.400000 | -0.409180 | 0.009180 |
| 0.9 | 0.901733 | -0.800000 | -0.803467 | 0.003467 |

Max absolute deviation `|<Z>_emp - <Z>_theory| = 0.0110 < 0.05` (PASS). Reproducible via `seed_simulator=42`.

### Experiment B — Performance micro-benchmark

Table 1 — sliding-window frequency estimator (paper Eq. 2): pure Python vs NumPy C-backend.

| Sequence Length | Pure Python (ms) | System-Level (ms) | Speedup |
|---:|---:|---:|---:|
| 10,000 | 4.76 | 0.45 | 10.5x |
| 100,000 | 51.50 | 5.96 | 8.6x |
| 1,000,000 | 543.85 | 77.47 | 7.0x |

Table 2 — full Unibit fold: pure Python vs Rust FFI (`core/target/release/umos_core.dll`).

| Sequence Length | Pure Python (ms) | System-Level (ms) | Speedup |
|---:|---:|---:|---:|
| 10,000 | 10.40 | 3.13 | 3.3x |
| 100,000 | 114.62 | 38.62 | 3.0x |
| 1,000,000 | 1,180.72 | 398.66 | 3.0x |

Table 2 includes Python-side FFI marshaling; the compiled kernel is faster still, so these are conservative end-to-end lower bounds.
