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
| 0.1000 | 0.095459 | 0.800000 | 0.809082 | 0.009082 |
| 0.3000 | 0.296875 | 0.400000 | 0.406250 | 0.006250 |
| 0.5000 | 0.505493 | 0.000000 | -0.010986 | 0.010986 |
| 0.7000 | 0.704590 | -0.400000 | -0.409180 | 0.009180 |
| 0.9000 | 0.901733 | -0.800000 | -0.803467 | 0.003467 |

**Max absolute deviation `|<Z>_emp - <Z>_theory| = 0.0110 < 0.05` (PASS).** The experiment uses a fixed simulator seed (`seed_simulator=42`), so the numbers above are exactly reproducible across runs. The empirical measurement probabilities converge to the theoretical weights within binomial sampling variance, confirming the classical preprocessing pipeline correctly initializes quantum state amplitudes.

### Experiment B — Performance Micro-Benchmark

`experiments/benchmark_unibit.py` benchmarks two identical functions on both sides of the comparison (apples-to-apples).

```bash
python experiments/benchmark_unibit.py
```

**Table 1 — Sliding-window frequency estimator (paper Eq. 2): Pure Python vs NumPy C-backend**

| Sequence Length | Pure Python (ms) | System-Level (ms) | Speedup |
|----------------:|-----------------:|------------------:|--------:|
| 10,000 | 4.76 | 0.45 | 10.5x |
| 100,000 | 51.50 | 5.96 | 8.6x |
| 1,000,000 | 543.85 | 77.47 | 7.0x |

**Table 2 — Full Unibit fold (repo engine): Pure Python vs Rust FFI (`core/target/release/umos_core.dll`)**

| Sequence Length | Pure Python (ms) | System-Level (ms) | Speedup |
|----------------:|-----------------:|------------------:|--------:|
| 10,000 | 10.40 | 3.13 | 3.3x |
| 100,000 | 114.62 | 38.62 | 3.0x |
| 1,000,000 | 1,180.72 | 398.66 | 3.0x |

> Note: Table 2 includes Python-side FFI marshaling (per-element normalization + ctypes buffer construction); the pure Rust kernel is faster still, so these speedups are a conservative end-to-end lower bound.

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
