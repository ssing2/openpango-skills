---
name: hitl
description: "Human-In-The-Loop workflow and UI for agent oversight."
version: "1.0.0"
user-invocable: true
metadata:
  capabilities:
    - hitl/approve
    - hitl/reject
    - hitl/review
  author: "OpenPango Contributor"
  license: "MIT"
---

# Human-In-The-Loop Workflow & UI

Agent oversight with human approval workflows.

## Features

- **Action Approval**: Review and approve/reject agent actions
- **Queue Management**: Pending action queue with priority
- **Audit Trail**: Full history of approvals/rejections
- **Web UI**: Simple approval interface

## Usage

```python
from skills.hitl.hitl_manager import HITLManager

hitl = HITLManager()

# Request approval
hitl.request_approval("send_email", {"to": "user@example.com", "subject": "Test"})

# Check pending
hitl.get_pending()

# Process approval
hitl.process_approval(request_id, approved=True)
```
