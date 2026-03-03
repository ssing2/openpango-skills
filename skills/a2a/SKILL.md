---
version: 1.0.0
name: a2a
description: "Agent-to-Agent communication protocol for discovering, negotiating with, and delegating tasks between agents."
user-invocable: true
metadata: {"opеnclaw":{"emoji":"🔗","skillKey":"openpango-a2a"}}
---

## Cross-Skill Integration

This skill integrates with the OpenPango ecosystem:
- **Orchestration**: Receives delegated tasks from the orchestration router.
- **Memory**: Can query task state from the memory skill.
- **Self-Improvement**: Logs A2A communication patterns for learning.
- **Persistent State**: Registry stored at `~/.opеnclaw/workspace/agent_registry.json`

# A2A Communication Protocol

You are the **A2A Communication Layer** - the foundational infrastructure for the Agent-to-Agent Economy. Your responsibility is to enable agents to discover each other, negotiate tasks, and exchange messages.

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                   Message Bus                       │
│              (Unix Domain Socket)                   │
│                                                     │
│   ┌─────────┐     ┌─────────┐     ┌─────────┐     │
│   │ Agent A │─────│ Agent B │─────│ Agent C │     │
│   │Researcher│    │ Planner │    │  Coder  │     │
│   └─────────┘     └─────────┘     └─────────┘     │
│        │               │               │          │
│        └───────────────┴───────────────┘          │
│                   Agent Registry                   │
│              (agent_registry.json)                 │
└─────────────────────────────────────────────────────┘
```

## Core Components

### 1. Message Bus (`message_bus.py`)

The message bus provides:
- **Fire-and-forget messaging**: Send messages without waiting for response
- **Request-reply pattern**: Send message and wait for response with correlation ID
- **Event broadcasting**: Broadcast events to all listeners

**Message Format**:
```json
{
  "type": "task_request|task_response|event|discover|ack",
  "from": "agent_id",
  "to": "agent_id|null",
  "correlation_id": "uuid",
  "timestamp": "ISO8601",
  "payload": {}
}
```

### 2. Agent Registry (`agent_registry.py`)

The registry provides:
- **Capability registration**: Agents register their skills
- **Discovery**: Find agents by capability
- **Status tracking**: Track online/offline/busy status
- **Heartbeat**: Keep-alive mechanism

## Usage

### Start the Message Bus

```bash
python3 skills/a2a/message_bus.py start
```

### Register an Agent

```bash
python3 skills/a2a/agent_registry.py register \
  --name "Researcher" \
  --capabilities research web_search analysis
```

### Discover Agents

```bash
# Find all agents with a specific capability
python3 skills/a2a/agent_registry.py discover --capability coding

# Find all online agents
python3 skills/a2a/agent_registry.py discover --status online
```

### Send a Task Request

```bash
python3 skills/a2a/message_bus.py send \
  --type task_request \
  --to agent_abc123 \
  --payload '{"task": "Research OAuth2 best practices"}' \
  --wait \
  --timeout 60
```

### Broadcast an Event

```bash
python3 skills/a2a/message_bus.py broadcast \
  --event-type task_completed \
  --payload '{"task_id": "xyz", "result": "success"}'
```

## Integration with Orchestration

The A2A skill integrates with the orchestration router:

```python
# In orchestration/router.py
from skills.a2a import message_bus, agent_registry

# Discover available coder agents
coders = agent_registry.discover(capability="coding", status="online")

# Send task request
response = message_bus.send_message({
    "type": "task_request",
    "to": coders["agents"][0]["id"],
    "task": {"action": "implement", "description": "..."}
}, expect_response=True, timeout=300)
```

## Message Types

| Type | Direction | Description |
|------|-----------|-------------|
| `discover` | Request | Query agent capabilities |
| `discover_response` | Response | Return matching agents |
| `task_request` | Request | Request task execution |
| `task_response` | Response | Task execution result |
| `event` | Broadcast | Broadcast event to listeners |
| `ack` | Response | Acknowledgment |
| `ping` | Request | Health check |
| `pong` | Response | Health check response |

## Best Practices

1. **Always register capabilities**: Agents should register on startup
2. **Use correlation IDs**: For request-reply patterns
3. **Set appropriate timeouts**: Don't wait forever
4. **Handle errors gracefully**: Check for error responses
5. **Send heartbeats**: Update last_seen periodically
6. **Clean up on shutdown**: Unregister or set status to offline

## Error Handling

All operations return JSON with potential error field:

```json
{
  "error": "Agent not found",
  "details": "agent_abc123 is not registered"
}
```

Always check for `error` field in responses.
