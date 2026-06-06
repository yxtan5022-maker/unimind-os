# unimind-os

English | [简体中文](README.zh-CN.md) | [Русский](README.ru.md)

The World's First AI Native Operating System. Breaking the wall between hardware and consciousness.

🌌 UniMind OS (UMOS)

The Post-Silicon Intelligence Layer

📖 Introduction

UniMind OS (UMOS) is not a traditional OS; it is a fundamental reconstruction of computer science. We shift from "software running on hardware" to "AI replacing the OS", morphing binary logic into a fluid topological mapping.

🚀 Core Vision

1. AI as System
Discard apps; AI generates and runs code instantly based on intent. Natural language replaces icons; the model replaces the kernel.

2. Universal AI-VM
No more Android/iOS barriers. AI generates mid-layer code on the fly to run any app on any device.

3. Fluid Hardware Adaptation
AI flows across devices, performing deep customization by writing new low-level code for specific hardware.

🛠️ Technical Modules

| Module | Language | Description |
|--------|----------|-------------|
| `umos_py/` | Python | Core dynamic bit-weighting engine (Unibit), entropy-weighted folding + collapse |
| `bridge/` | Python | LLM code generation, cross-architecture VM, hardware resonance driver |
| `quantum/` | Python | Qiskit-based quantum circuit mapping of Unibit logic |
| `core/` | Rust | Accelerated Unibit via FFI (optional, auto-detected by Python) |
| `kernel/` | C++ | Topology Mapper with real CPU/OS/RAM detection |

📚 Docs

- Roadmap: [ROADMAP.md](ROADMAP.md)
- Whitepaper: [docs/WHITE_PAPER.md](docs/WHITE_PAPER.md)

## 🚀 Quick Start

```bash
# Clone and run the demo immediately
git clone https://github.com/yxtan5022-maker/unimind-os.git
cd unimind-os

# Option A — run directly
pip install -e .          # install package + CLI
python run.py             # core folding/collapse demo
python example/proof_of_concept.py
python bridge/agent_resonance.py   # real hardware detection
python bridge/cross_arch_vm.py     # host architecture info
python bridge/umos_link.py         # LLM code generation

# Option B — install as a package
umos-demo
```

## 🤖 LLM Integration ("AI as Kernel")

Set environment variables to use a real LLM for code generation:

```bash
export UMOS_LLM_API_KEY="sk-..."
export UMOS_LLM_BASE_URL="https://api.openai.com/v1"  # or Ollama, etc.
export UMOS_LLM_MODEL="gpt-4o-mini"                    # default

python bridge/umos_link.py
```

The bridge will translate natural-language intent into runnable Python code.

## 🧪 Demo

### Python

```bash
# Core logic folding + collapse
python -m umos_py.demo

# Proof-of-concept
python example/proof_of_concept.py

# AI Agent resonance (real hardware topology)
python bridge/agent_resonance.py

# Cross-architecture VM (real host detection)
python bridge/cross_arch_vm.py

# LLM code generation bridge
python bridge/umos_link.py

# Quantum circuit mapping (requires qiskit)
pip install umos[quantum]
python -c "from quantum.qunibit import demo; demo()"
```

### Rust core (optional, for Python acceleration / ABI)

**Prerequisites:** Install Rust via [rustup.rs](https://rustup.rs).

```bash
cd core
cargo build --release
```

Python will auto-load the built library:

- Windows: `core/target/release/umos_core.dll`
- Linux: `core/target/release/libumos_core.so`
- macOS: `core/target/release/libumos_core.dylib`

### C++ kernel (Topology Mapper) — real hardware detection

**Prerequisites:** CMake 3.16+ and a C++17 compiler.

```bash
# Linux / macOS
cmake -S . -B build
cmake --build build --config Release
./build/kernel/umos_topo_mapper

# Windows (MinGW)
cmake -S . -B build -G "MinGW Makefiles" -DCMAKE_MAKE_PROGRAM="C:\msys64\mingw64\bin\mingw32-make.exe"
cmake --build build --config Release
./build/kernel/umos_topo_mapper.exe
```

The mapper detects real CPU cores, OS type, and physical RAM at runtime.

### One-shot build

```bash
python build.py
```

## 🧪 Tests

```bash
pip install pytest
python -m pytest tests/ -v
```

## 🔬 Quantum Computing

The `quantum/` module maps Unibit's fold/collapse onto quantum circuits using Qiskit:

```python
from quantum.qunibit import QUnibit

qu = QUnibit()
qc = qu.fold_bits_circuit([1, 0, 1, 1, 0, 1, 0, 0, 1, 1])
result = qu.simulate(qc)  # runs on AerSimulator
print(result)
```

Classical → quantum mapping:

| Classical | Quantum |
|-----------|---------|
| `fold_bits` (entropy-weighted folding) | `QuantumCircuit` with `ry` rotations by bit |
| `collapse_signal` (threshold) | Measurement + projection |

## 🤝 Contributing

We are looking for architects, dreamers, and hackers who believe that the "Wall" must come down.

**Join the revolution. Define the OS of the future.**
