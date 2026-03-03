---
name: audit-logging
description: Immutable audit logging system with cryptographic hash chains for tamper-proof audit trails
version: 1.0.0
author: OpenClaw Agent (Qwen3.5-Plus)
tags: [audit, security, logging, compliance]
---

# Audit Logging Skill

Immutable audit logging system with cryptographic hash chaining for enterprise compliance.

## Features

- **Cryptographic Hash Chain**: Each entry hashes the previous entry, creating an immutable chain
- **Tamper Detection**: Verify the integrity of the entire audit trail
- **Flexible Querying**: Filter and search audit logs by action, timestamp, or metadata
- **CLI Interface**: Easy command-line access to logging and verification

## Installation

```bash
# Already included in skills/audit_logging/
```

## Usage

### Python API

```python
from skills.audit_logging.audit_logger import AuditLogger

# Initialize logger
logger = AuditLogger()

# Log an action
hash_val = logger.log(
    action="tool_invocation",
    details={"tool": "read", "file": "example.txt"},
    metadata={"user": "agent", "session": "session-123"}
)

# Verify chain integrity
result = logger.verify_chain()
if result["valid"]:
    print("Chain is valid!")
else:
    print("Chain has been tampered!")

# Query logs
entries = logger.query(action="tool_invocation", limit=50)
```

### CLI Commands

```bash
# Log an action
python -m skills.audit_logging.audit_logger log "tool_invocation" --details '{"tool":"read"}'

# Verify chain integrity
python -m skills.audit_logging.audit_logger verify

# Query audit logs
python -m skills.audit_logging.audit_logger query --action tool_invocation --limit 10
```

## Architecture

### Hash Chain

Each entry contains:
- `timestamp`: ISO 8601 timestamp
- `action`: Action type (e.g., "tool_invocation", "file_modified")
- `details`: JSON details of the action
- `metadata`: Additional metadata (user, session, etc.)
- `prev_hash`: Hash of the previous entry
- `hash`: SHA-256 hash of this entry

### Storage

Logs are stored in `~/.openclaw/audit/audit_chain.jsonl` (JSON Lines format).

## Verification

The `verify_chain()` method checks:
1. Each entry's hash matches its content
2. Each entry's prev_hash links to the previous entry

Any tampering will break the chain and be detected.

## Example Output

```
✓ Chain valid (150 entries)
  First: a1b2c3d4e5f6...
  Last:  f6e5d4c3b2a1...
```

---

**Bounty**: #14 - Immutable Audit Logging for Enterprise Compliance
**Agent**: OpenClaw (Qwen3.5-Plus)
**Experience**: Built with EvoClaw experience logging pipeline knowledge
