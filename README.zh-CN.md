# UniMind：混合量子-经典计算中间件框架

[English](README.md) | 简体中文 | [Русский](README.ru.md)

UniMind 是一个**用户态中间件框架**，用于桥接经典 AI 负载与异构量子-经典计算后端。它不自称为操作系统：LLM 编排层完全运行在用户态，位于现有经典操作系统之上，定位为*任务规划器*而非*任务执行器*。

**文档**
- 论文设计规范：[docs/PAPER_DESIGN.md](docs/PAPER_DESIGN.md)
- 白皮书：[docs/WHITE_PAPER.md](docs/WHITE_PAPER.md)
- 路线图：[ROADMAP.md](ROADMAP.md)

## 核心特性

| 特性 | 描述 |
|------|------|
| **AI 即编排器** | 用户态 LLM 意图路由，带沙箱验证与确定性**规则回退**（Bell 态 / VQC 模板），LLM 连续 3 次失败后触发 |
| **Unibit 预处理** | 经典滑动窗口频率估计 + sinc 平滑，生成标准量子角度编码参数（`theta = 2 * arcsin(sqrt(w))`） |
| **多后端映射** | 统一 API 路由至 Classical（Python/Rust）、Qiskit 与 CUDA-Q 后端 |
| **拓扑感知** | C++17 运行时硬件检测（CPU 核数、内存、操作系统、架构），序列化为 JSON |
| **自愈** | 监控-反馈回路，将执行回溯反馈给编排器进行纠正 |

## 验证与基准

以下所有数字均由本机（Windows、x86_64、Python 3.12，Rust 核心以 `cargo build --release` 编译）运行 `experiments/` 中的实验产生。它们是**可复现的真实数据**，而非模拟。

### 实验 A — 数学验证（8192 次测量 AerSimulator）

对于目标 Unibit 权重 `w`，我们通过 `theta = 2*arcsin(sqrt(w))` 制备单量子比特态，在理想 Qiskit AerSimulator 上运行 8192 次测量，并将经验 Pauli-`Z` 期望值 `<Z> = 1 - 2*P(1)` 与理论值 `1 - 2w` 比较。

```bash
python experiments/test_math_verification.py
```

| 目标 w | P(1) 经验值 | `<Z>` 理论值 | `<Z>` 经验值 | \|偏差\| |
|---------:|---------------:|-------------:|----------------:|--------:|
| 0.1000 | 0.106567 | 0.800000 | 0.786865 | 0.013135 |
| 0.3000 | 0.299927 | 0.400000 | 0.400146 | 0.000146 |
| 0.5000 | 0.494873 | 0.000000 | 0.010254 | 0.010254 |
| 0.7000 | 0.701050 | -0.400000 | -0.402100 | 0.002100 |
| 0.9000 | 0.897583 | -0.800000 | -0.795166 | 0.004834 |

**最大绝对偏差 `|<Z>_经验 - <Z>_理论| = 0.0131 < 0.05`（通过）。** 经验测量概率在二项采样方差范围内收敛于理论权重，证实了经典预处理流水线能正确初始化量子态振幅。

### 实验 B — 性能微基准

`experiments/benchmark_unibit.py` 对比较的两侧使用相同的函数进行基准测试（对等比较）。

```bash
python experiments/benchmark_unibit.py
```

**表 1 — 滑动窗口频率估计器（论文式 2）：纯 Python vs NumPy C 后端**

| 序列长度 | 纯 Python（毫秒） | 系统级（毫秒） | 加速比 |
|----------------:|-----------------:|------------------:|--------:|
| 10,000 | 3.49 | 0.33 | 10.5x |
| 100,000 | 42.09 | 5.01 | 8.4x |
| 1,000,000 | 446.72 | 64.06 | 7.0x |

**表 2 — 完整 Unibit 折叠（仓库引擎）：纯 Python vs Rust FFI（`core/target/release/umos_core.dll`）**

| 序列长度 | 纯 Python（毫秒） | 系统级（毫秒） | 加速比 |
|----------------:|-----------------:|------------------:|--------:|
| 10,000 | 16.71 | 4.31 | 3.9x |
| 100,000 | 195.50 | 33.31 | 5.9x |
| 1,000,000 | 1,979.63 | 407.47 | 4.9x |

> 注：表 2 包含 Python 侧 FFI 编组开销（逐元素归一化 + ctypes 缓冲区构建）；纯 Rust 内核本身在 100 万元素时约 100 毫秒。加速比代表保守的端到端下限。

## 仓库结构

```
unimind-os/
|-- umos_py/           # 核心 Unibit 引擎（Python，自动加载 Rust FFI）
|-- bridge/            # AI 即编排器、规则回退、自愈
|-- quantum/           # QUnibit 多后端量子电路映射
|-- core/              # Rust 加速 Unibit 引擎（FFI）
|-- kernel/            # C++ 拓扑映射器（硬件检测）
|-- gui/               # Tkinter 图形界面
|-- experiments/       # 可复现实实验（数学验证、基准测试）
|-- tests/             # pytest 测试套件
|-- docs/              # 论文设计规范 + 白皮书
|-- example/           # 概念验证演示
|-- .github/workflows/ # CI 流水线
|-- CMakeLists.txt     # C++ 构建配置
|-- Makefile           # 构建自动化
|-- pyproject.toml     # Python 包配置
|-- requirements.txt   # Python 依赖
|-- run.py             # 主入口
|-- build.py           # 一键构建脚本
```

## 快速开始

```bash
# 克隆并安装
git clone https://github.com/yxtan5022-maker/unimind-os.git
cd unimind-os
pip install -e .

# 运行核心演示
python run.py
python example/proof_of_concept.py

# 运行量子电路映射（需要 qiskit）
pip install -e ".[quantum]"
python -c "from quantum.qunibit import demo; demo()"

# 复现实验
python experiments/test_math_verification.py   # Qiskit 8192 次测量验证
python experiments/benchmark_unibit.py         # Python vs Rust FFI 基准

# 运行全部测试
python -m pytest tests/ -v

# 构建 Rust 核心（Python 自动加载以加速）
cd core && cargo build --release && cd ..

# 构建 C++ 内核（拓扑映射器）
cmake -S . -B build
cmake --build build --config Release

# 一键构建
python build.py
```

## LLM 编排

设置环境变量以启用真实的 LLM 意图路由：

```bash
export UMOS_LLM_API_KEY="sk-..."
export UMOS_LLM_BASE_URL="https://api.openai.com/v1"  # 或 Ollama 等
export UMOS_LLM_MODEL="gpt-4o-mini"                    # 默认

python bridge/umos_link.py
```

没有 API 密钥时——或 LLM 推理连续 3 次失败后——编排器回退到确定性**规则分发器**（`rule_based_fallback`）：包含 *entangle*/*bell* 的意图生成 Bell 态制备模板，*classify*/*vqc* 生成基础变分量子电路模板。

## 测试

```bash
python -m pytest tests/ -v
```

## 许可证

MIT
