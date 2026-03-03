---
name: stealth
description: "Anti-fingerprinting CDP stealth router and visual DOM abstraction."
version: "1.0.0"
user-invocable: true
metadata:
  capabilities:
    - stealth/fingerprint
    - stealth/cdp
    - stealth/dom
  author: "OpenPango Contributor"
  license: "MIT"
---

# Anti-Fingerprinting Stealth Engine

CDP stealth router and visual DOM abstraction for undetectable browsing.

## Features

- **Fingerprint Randomization**: Canvas, WebGL, Audio, Font
- **CDP Stealth Router**: Route CDP commands through stealth layer
- **Visual DOM Abstraction**: Hide real DOM structure
- **User Agent Spoofing**: Rotate user agents

## Usage

```python
from skills.stealth.stealth_engine import StealthEngine

engine = StealthEngine()

# Start stealth session
session = engine.create_session()

# Apply fingerprint randomization
engine.apply_randomization(session, ["canvas", "webgl", "audio"])

# Navigate stealthily
engine.navigate(session, "https://example.com")
```
