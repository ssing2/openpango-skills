---
name: credentials
description: "Dynamic credentials management for agent integrations."
version: "1.0.0"
user-invocable: true
metadata:
  capabilities:
    - credentials/store
    - credentials/retrieve
    - credentials/rotate
  author: "OpenPango Contributor"
  license: "MIT"
---

# Dynamic Credentials Manager

Secure credentials management with dynamic integration support.

## Features

- **Dynamic Storage**: Store credentials in encrypted database
- **Multiple Providers**: Support for Email, Telegram, Discord, Slack, etc.
- **Auto-Fallback**: Fallback to environment variables if not in database
- **Rotation Support**: Automatic credential rotation

## Usage

```python
from skills.credentials.credential_manager import CredentialManager

creds = CredentialManager()

# Store credentials
creds.store("telegram", {"bot_token": "xxx"})

# Retrieve credentials
token = creds.get("telegram", "bot_token")
```
