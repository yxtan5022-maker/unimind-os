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

/core/lib-unibit — Math Foundation

- Dynamic Bit-Weighting: Implements "logic collapse" where bits are weighted by entropy.
- Virtual Expansion: Simulates 64GB logical throughput on 32GB RAM via mathematical mapping.

/kernel/topo-mapper — Topology Engine

- Hardware Transparency: Converts AI computation graphs into abstract topological manifolds.
- Real-time Scaling: Automatically identifies CPU/GPU/NPU and stretches/compresses binary streams to fit the physical structure.

📚 Docs

- Roadmap: [ROADMAP.md](ROADMAP.md)
- Whitepaper: [docs/WHITE_PAPER.md](docs/WHITE_PAPER.md)

## 🚀 Quick Start

```bash
# Clone and run the demo immediately
git clone https://github.com/yxtan5022-maker/unimind-os.git
cd unimind-os

# Option A — run directly
python run.py
python emample/proof_of_concept.py
python bridge/umos_link.py
python bridge/cross_arch_vm.py
python bridge/agent_resonance.py

# Option B — install as a package
pip install -e .
umos-demo
```

## 🧪 Demo

### Python

```bash
# Core logic folding + collapse demo
python -m umos_py.demo

# Proof-of-concept: 32GB → 64GB logical expansion
python emample/proof_of_concept.py

# AI Agent resonance bridge
python bridge/umos_link.py

# Cross-architecture virtual machine
python bridge/cross_arch_vm.py

# Hardware resonance driver
python bridge/agent_resonance.py
```

### Rust core (optional, for Python acceleration / ABI)

**Prerequisites:** Install Rust via [rustup.rs](https://rustup.rs).

```bash
cd core
cargo build --release
```

After a successful build, Python will auto-try loading:

- Windows: `core/target/release/umos_core.dll`
- Linux: `core/target/release/libumos_core.so`
- macOS: `core/target/release/libumos_core.dylib`

### C++ kernel (Topology Mapper)

**Prerequisites:** CMake 3.16+ and a C++17 compiler (GCC, Clang, or MSVC).

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

## 🤝 Contributing
We are looking for architects, dreamers, and hackers who believe that the "Wall" must come down. 

**Join the revolution. Define the OS of the future.**
