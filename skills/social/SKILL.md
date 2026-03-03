---
name: social
description: "Comprehensive social media integration (Twitter, LinkedIn, Farcaster)."
version: "1.0.0"
user-invocable: true
metadata:
  capabilities:
    - social/twitter
    - social/linkedin
    - social/farcaster
  author: "OpenPango Contributor"
  license: "MIT"
---

# Social Media Core Skill

Multi-platform social media integration.

## Features

- **Twitter/X**: Post tweets, threads, reply
- **LinkedIn**: Share posts, articles
- **Farcaster**: Casts, reactions

## Configuration

| Environment Variable | Description |
|---------------------|-------------|
| `TWITTER_API_KEY` | Twitter API key |
| `TWITTER_API_SECRET` | Twitter API secret |
| `LINKEDIN_ACCESS_TOKEN` | LinkedIn access token |
| `FARCASTER_MNEMONIC` | Farcaster wallet mnemonic |

## Usage

```python
from skills.social.social_manager import SocialManager

social = SocialManager()

# Post to Twitter
social.post("twitter", "Hello world!")

# Post to LinkedIn
social.post("linkedin", "Professional update")

# Get timeline
social.get_timeline("twitter")
```
