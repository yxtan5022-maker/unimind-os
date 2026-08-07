# UniMind Roadmap

English | [简体中文](ROADMAP.zh-CN.md)

UniMind is a user-space quantum-classical middleware research prototype. This roadmap tracks the real, currently-scoped engineering work. It deliberately excludes fabricated features (no "AI-native OS", no virtual memory expansion, no kernel bypass).

## Phase 1: Core Alignment (Current)

* **Unibit correctness:** Sliding-window frequency (Eq. 2), sinc folding (Eq. 3), and collapse (Eq. 4) implemented identically in Python and the Rust FFI engine; verified by 42 automated pytest tests and a Python-vs-Rust equality check.
* **Mathematical verification:** Qiskit AerSimulator experiment with a fixed seed showing empirical measurement frequencies converge to theoretical weights (`|<Z>_emp - <Z>_theory| = 0.0110 < 0.05`).
* **Performance benchmarks:** NumPy speedup 7.0x-10.5x; Rust FFI end-to-end speedup 3.0x-3.3x over pure Python.
* **Honest sandbox:** Restricted-namespace executor with static-analysis rejection of risky patterns; rule-based fallback; honest "not supported" responses for unsupported intent actions.
* **Hardware probe:** `kernel/topo_mapper.cpp` emits JSON host detection (cores, OS, arch, RAM).

## Phase 2: Robustness and Coverage

* **Backend breadth:** Systematic testing of the quantum backend matrix (qiskit classical/aer/ibm, cudaq) and graceful degradation when a backend is absent.
* **Orchestrator reliability:** Improve LLM plan validation and the rule-based fallback; document failure modes honestly.
* **Cross-platform packaging:** Verify Windows/macOS/Linux builds of the Rust FFI DLL and the launcher scripts.

## Phase 3: Research Directions

* **Encoding studies:** Evaluate alternate smoothing windows and collapse thresholds on the quality of downstream encoding.
* **Noise sensitivity:** Measure how measurement noise affects recovered frequencies on real (non-ideal) backends.
* **Integration:** Wire the hardware probe and precision selection into the orchestration path end-to-end.
