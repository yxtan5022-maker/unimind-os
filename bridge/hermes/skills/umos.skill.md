# UMOS (Unified Mind Operating System)

Connect to a running UMOS node and access its AI-native kernel capabilities — folding, collapse, expand, compute, quantum sampling, self-healing, cluster offloading, and logical context migration.

## Overview

UMOS is an AI-native OS kernel that exposes computational primitives through the **Intent Execution Protocol (IEP)**. This skill allows Hermes Agent to discover and call UMOS operations on any reachable node on the LAN.

### Prerequisites

- A running UMOS node on the LAN (`python -m bridge.hermes.mcp_server`)
- Or a UMOS Desktop EXE instance with MCP enabled
- Network multicast enabled (for cluster discovery)

## Usage

### `/umos status`

Get the current UMOS node's status — CPU, RAM, precision level, and capabilities.

```
/umos status
```

### `/umos fold [bits]`

Fold classical bits into quantum-like probability amplitudes using sine interpolation.

```
/umos fold 1 0 1 1 0 1
```

### `/umos collapse [values]`

Collapse folded amplitudes back to classical bits via threshold.

```
/umos collapse 0.7071 0.0000 0.7071 0.0000
```

### `/umos expand [values] [factor]`

Expand a signal by virtual interpolation factor.

```
/umos expand 0.7071 0.0000 0.7071 0.0000 2
```

### `/umos compute [python code]`

Execute Python code on UMOS. The result is captured and returned. Self-healing is automatic on failure.

```
/umos compute "result = sum(i * i for i in range(100))"
```

### `/umos quantum [backend] [shots]`

Run a quantum circuit sample using the specified backend (`qiskit` or `cudaq`).

```
/umos quantum qiskit 1024
```

### `/umos heal [code]`

Send broken code to UMOS for LLM-assisted auto-repair.

```
/umos heal "result = 1/0"
```

### `/umos topology`

List all alive UMOS cluster peers and their logical weights.

### `/umos migrate [key=value ...]`

Migrate a logical context to another cluster node.

```
/umos migrate user_preference=dark intent=research
```

## MCP Integration

If you've connected UMOS as an MCP server, you can use the tools directly without slash commands:

```
Use the `umos_fold` tool to fold bits [1,0,1,1] into amplitudes.
Then use `umos_expand` with factor 3 on the result.
```

## Configuration

No special configuration is required. The MCP server autodetects cluster nodes via UDP multicast on `239.255.77.77:7777`.

To start the MCP server manually:

```bash
python -m bridge.hermes.mcp_server
```

Or via the UMOS Desktop EXE with the `--mcp` flag.

## Example Session

**User:** `/umos status`

**Agent:**
```
Node: umos-a1b2c3
CPU: 23.4% | RAM: 61.2% | Precision: fp32
Capabilities: fold, collapse, compute, quantum
Cluster: 3 peers alive
```

**User:** `/umos fold 1 0 1 1 0 1 0 0 1 1`

**Agent:**
```
Folded: [0.7071, 0.0000, 0.7071, 0.0000, 0.5878, 0.0000, 0.0000, 1.0000, 0.7071, 0.0000, ...]
```

**User:** `/umos compute "result = sum(range(1000))"`

**Agent:**
```
Result: 499500 (2.1ms, computed locally)
```
