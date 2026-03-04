---
name: simulation
version: 1.0.0
description: "OpenClaw bridge to spatial Reinforcement Learning environments (Gymnasium)."
dependencies: []
---

# Simulation Bridge

This skill provides an interface to Gymnasium (OpenAI Gym), allowing autonomous agents to explore spatial and continuous environments to advance reasoning and long-term planning safely.

## Files
- `game_bridge.py`: Python module exposing `initialize`, `step`, and `reset` functions.

## Capabilities
- Environment initializations for classic control systems (e.g. `CartPole-v1`).
- JSON serialization of complex NumPy environment observations.
- Execution of discrete actions.
