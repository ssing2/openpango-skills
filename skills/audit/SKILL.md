---
name: audit
description: "Immutable audit logging for enterprise compliance."
version: "1.0.0"
user-invocable: true
metadata:
  capabilities:
    - audit/log
    - audit/verify
    - audit/report
  author: "OpenPango Contributor"
  license: "MIT"
---

# Immutable Audit Logging Skill

Enterprise-grade audit logging with cryptographic verification.

## Features

- **Immutable Logs**: Append-only with hash chaining
- **Digital Signatures**: RSA/ECDSA signature verification
- **Timestamp Proof**: RFC 3161 timestamp authority
- **Compliance Reports**: SOC2, HIPAA, GDPR

## Configuration

| Environment Variable | Description |
|---------------------|-------------|
| `AUDIT_LOG_PATH` | Audit log file path |
| `AUDIT_SIGN_KEY` | Signing private key |
| `AUDIT_VERIFY_KEY` | Verification public key |

## Usage

```python
from skills.audit.audit_logger import AuditLogger

logger = AuditLogger()

# Log event
logger.log("user_login", user="alice", ip="192.168.1.1")

# Verify integrity
logger.verify()

# Export report
logger.export_report("compliance_report.json")
```
