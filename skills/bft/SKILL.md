---
name: bft
description: "Byzantine Fault Tolerant mesh network for agent delegation."
version: "1.0.0"
user-invocable: true
metadata:
  capabilities:
    - bft/consensus
    - bft/mesh
    - bft/delegate
  author: "OpenPango Contributor"
  license: "MIT"
---

# BFT Mesh Network for Agent Delegation

Byzantine Fault Tolerant mesh network for distributed agent coordination.

## Features

- **PBFT Consensus**: Practical Byzantine Fault Tolerance
- **Mesh Networking**: Peer-to-peer agent communication
- **Delegation Protocol**: Task delegation across agents
- **Fault Tolerance**: Handles up to f Byzantine nodes

## Usage

```python
from skills.bft.bft_network import BFTNetwork

network = BFTNetwork(node_id="agent-1")

# Start network
network.start()

# Propose task
network.propose("task_id", {"action": "compute", "data": [...]})

# Get consensus result
result = network.get_result("task_id")
```
