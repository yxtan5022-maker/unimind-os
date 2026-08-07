# UMOS Node (UniMind Middleware)

Connect to a running UniMind node and access its user-space capabilities — fold, collapse, compute, quantum sampling, self-healing, cluster status, and context migration.

## Overview

UniMind is a user-space quantum-classical middleware research prototype (not an operating system). It exposes computational primitives through the **Intent Execution Protocol (IEP)**. This skill allows Hermes Agent to discover and call UniMind operations on any reachable node on the LAN.

### Prerequisites

- A running UniMind node on the LAN (`python -m bridge.hermes.mcp_server`)
- Or a UniMind Desktop EXE instance with MCP enabled
- Network multicast enabled (for cluster discovery)

## Usage

### `/umos status`

Get the current node's status — CPU, RAM, precision level, and capabilities.

```
/umos status
```

### `/umos fold [bits]`

Fold classical bits into a smoothed signal via sliding-window frequency and sinc envelope (paper Eqs. 2-3).

```
/umos fold 1 0 1 1 0 1
```

### `/umos collapse [values]`

Threshold folded signal values back to discrete bits (paper Eq. 4).

```
/umos collapse 0.7071 0.0000 0.7071 0.0000
```

### `/umos compute [python code]`

Execute Python code on the node. The result is captured and returned. Self-healing is automatic on failure.

```
/umos compute "result = sum(i * i for i in range(100))"
```

### `/umos quantum [backend] [shots]`

Run a quantum circuit sample using the specified backend (`qiskit` or `cudaq`).

```
/umos quantum qiskit 1024
```

### `/umos heal [code]`

Send broken code to the node for LLM-assisted auto-repair.

```
/umos heal "result = 1/0"
```

### `/umos topology`

List all alive cluster peers and their logical weights.

### `/umos migrate [key=value ...]`

Migrate a logical context to another cluster node.

```
/umos migrate user_preference=dark intent=research
```

## MCP Integration

If you've connected UniMind as an MCP server, you can use the tools directly without slash commands:

```
Use the `umos_fold` tool to fold bits [1,0,1,1] into amplitudes.
Then use `umos_collapse` on the result.
```

Note: `umos_expand` is not a supported operation; it is not part of the Unibit definition and is not exposed.

## Configuration

No special configuration is required. The MCP server autodetects cluster nodes via UDP multicast on `239.255.77.77:7777`.

To start the MCP server manually:

```bash
python -m bridge.hermes.mcp_server
```

Or via the UniMind Desktop EXE with the `--mcp` flag.

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
