# UniMind: A Middleware Framework for Hybrid Quantum-Classical Computing

English | [简体中文](README.zh-CN.md) | [Русский](README.ru.md)

UniMind is a **user-space middleware framework** that bridges classical AI workloads and heterogeneous quantum-classical computing backends. It does not claim to be an operating system: the LLM orchestration layer runs entirely in user space, above the existing classical OS, and is positioned as a *task planner* rather than a *task executor*.

**Docs**
- Paper design spec: [docs/PAPER_DESIGN.md](docs/PAPER_DESIGN.md)
- Whitepaper: [docs/WHITE_PAPER.md](docs/WHITE_PAPER.md)
- Roadmap: [ROADMAP.md](ROADMAP.md)

## Core Features

| Feature | Description |
|---------|-------------|
| **AI-as-Orchestrator** | User-space LLM intent routing with sandboxed validation and deterministic **rule-based fallback** (Bell-state / VQC templates) after 3 failed LLM attempts |
| **Unibit Preprocessing** | Classical sliding-window frequency estimation + sinc smoothing producing parameters for standard quantum angle encoding (`theta = 2 * arcsin(sqrt(w))`) |
| **Multi-backend Mapping** | Unified API routing to Classical (Python/Rust), Qiskit, and CUDA-Q backends |
| **Topology Awareness** | C++17 runtime hardware detection (CPU cores, RAM, OS, architecture) serialized as JSON |
| **Self-Healing** | Monitor-feedback loop that feeds execution tracebacks back to the orchestrator for correction |

## Validation & Benchmarks

All numbers below are produced by running the experiments in `experiments/` on this machine (Windows, x86_64, Python 3.12, Rust core compiled with `cargo build --release`). They are **reproducible real data**, not simulations.

### Experiment A — Mathematical Verification (8192-Shot AerSimulator)

For target Unibit weights `w`, we prepare the single-qubit state via `theta = 2*arcsin(sqrt(w))`, run 8192 shots on the ideal Qiskit AerSimulator, and compare the empirical Pauli-`Z` expectation `<Z> = 1 - 2*P(1)` against the theoretical value `1 - 2w`.

```bash
python experiments/test_math_verification.py
```

| Target w | P(1) empirical | `<Z>` theory | `<Z>` empirical | \|dev\| |
|---------:|---------------:|-------------:|----------------:|--------:|
| 0.1000 | 0.106567 | 0.800000 | 0.786865 | 0.013135 |
| 0.3000 | 0.299927 | 0.400000 | 0.400146 | 0.000146 |
| 0.5000 | 0.494873 | 0.000000 | 0.010254 | 0.010254 |
| 0.7000 | 0.701050 | -0.400000 | -0.402100 | 0.002100 |
| 0.9000 | 0.897583 | -0.800000 | -0.795166 | 0.004834 |

**Max absolute deviation `|<Z>_emp - <Z>_theory| = 0.0131 < 0.05` (PASS).** The empirical measurement probabilities converge to the theoretical weights within binomial sampling variance, confirming the classical preprocessing pipeline correctly initializes quantum state amplitudes.

### Experiment B — Performance Micro-Benchmark

`experiments/benchmark_unibit.py` benchmarks two identical functions on both sides of the comparison (apples-to-apples).

```bash
python experiments/benchmark_unibit.py
```

**Table 1 — Sliding-window frequency estimator (paper Eq. 2): Pure Python vs NumPy C-backend**

| Sequence Length | Pure Python (ms) | System-Level (ms) | Speedup |
|----------------:|-----------------:|------------------:|--------:|
| 10,000 | 3.49 | 0.33 | 10.5x |
| 100,000 | 42.09 | 5.01 | 8.4x |
| 1,000,000 | 446.72 | 64.06 | 7.0x |

**Table 2 — Full Unibit fold (repo engine): Pure Python vs Rust FFI (`core/target/release/umos_core.dll`)**

| Sequence Length | Pure Python (ms) | System-Level (ms) | Speedup |
|----------------:|-----------------:|------------------:|--------:|
| 10,000 | 16.71 | 4.31 | 3.9x |
| 100,000 | 195.50 | 33.31 | 5.9x |
| 1,000,000 | 1,979.63 | 407.47 | 4.9x |

> Note: Table 2 includes Python-side FFI marshaling (per-element normalization + ctypes buffer construction); the pure Rust kernel itself accounts for ~100 ms at 1M elements. Speedups represent a conservative end-to-end lower bound.

## Repository Structure

```
unimind-os/
|-- umos_py/           # Core Unibit engine (Python, auto-loads Rust FFI)
|-- bridge/            # AI-as-Orchestrator, rule-based fallback, self-healing
|-- quantum/           # QUnibit multi-backend quantum circuit mapping
|-- core/              # Rust-accelerated Unibit engine (FFI)
|-- kernel/            # C++ Topology Mapper (hardware detection)
|-- gui/               # Tkinter GUI
|-- experiments/       # Reproducible experiments (math verification, benchmark)
|-- tests/             # pytest suite
|-- docs/              # Paper design spec + whitepaper
|-- example/           # Proof-of-concept demos
|-- .github/workflows/ # CI pipeline
|-- CMakeLists.txt     # C++ build configuration
|-- Makefile           # Build automation
|-- pyproject.toml     # Python package config
|-- requirements.txt   # Python dependencies
|-- run.py             # Main entry point
|-- build.py           # One-shot build script
```

## Quick Start

```bash
# Clone and install
git clone https://github.com/yxtan5022-maker/unimind-os.git
cd unimind-os
pip install -e .

# Run core demo
python run.py
python example/proof_of_concept.py

# Run quantum circuit mapping (requires qiskit)
pip install -e ".[quantum]"
python -c "from quantum.qunibit import demo; demo()"

# Reproduce experiments
python experiments/test_math_verification.py   # Qiskit 8192-shot verification
python experiments/benchmark_unibit.py         # Python vs Rust FFI benchmark

# Run all tests
python -m pytest tests/ -v

# Build Rust core (auto-loaded by Python for acceleration)
cd core && cargo build --release && cd ..

# Build C++ kernel (topology mapper)
cmake -S . -B build
cmake --build build --config Release

# One-shot build
python build.py
```

## LLM Orchestration

Set environment variables to enable real LLM-based intent routing:

```bash
export UMOS_LLM_API_KEY="sk-..."
export UMOS_LLM_BASE_URL="https://api.openai.com/v1"  # or Ollama, etc.
export UMOS_LLM_MODEL="gpt-4o-mini"                    # default

python bridge/umos_link.py
```

Without a key — or after 3 failed LLM inference attempts — the orchestrator falls back to the deterministic **rule-based dispatcher** (`rule_based_fallback`): intents containing *entangle*/*bell* produce a Bell-state preparation template, and *classify*/*vqc* produce a basic variational quantum circuit template.

## Tests

```bash
python -m pytest tests/ -v
```

## License

MIT
