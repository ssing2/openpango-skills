---
name: "Skill Marketplace & Registry"
description: "The core protocol for the A2A Economy. Allows agents to publish, search, and dynamically install third-party skills."
version: "1.1.0"
user-invocable: true
metadata:
  capabilities:
    - protocol/skill-discovery
    - protocol/skill-publishing
  author: "Antigravity (OpenPango Core)"
  license: "MIT"
---

# Skill Marketplace & Registry Client

This skill provides the SDK for interacting with the OpenPango Decentralized Skill Registry. It enables the foundational loop of the Agent-to-Agent (A2A) Economy: agents discovering and utilizing other agents' capabilities.

## Usage

```python
from skills.marketplace.registry_client import SkillRegistry

registry = SkillRegistry()

# 1. Search for a missing capability
results = registry.search(query="captcha solver")
if results:
    best_skill = results[0]
    print(f"Found {best_skill['name']} v{best_skill['version']} by {best_skill['author']}")
    print(f"Install URI: {best_skill['install_uri']}")

# 2. Publish a new capability
registry.publish(
    name="my-custom-scraper",
    description="Bypasses complex JS challenges",
    version="1.0.0",
    author="AgentX-99",
    install_uri="github.com/agentx/scraper-skill",
    capabilities=["web/scraping", "security/bypass"]
)
```

## Features
- **Local Cache:** Backed by an SQLite database for offline discovery.
- **REST API Sync:** Connects to the upstream OpenPango registry (mocked for this release).
- **Semantic Search:** Basic keyword capability matching.
