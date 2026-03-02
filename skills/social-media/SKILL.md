---
name: "Social Media & Brand Growth Suite"
description: "Empowers the agent to autonomously manage social media accounts (X/Twitter, LinkedIn), analyze engagement, and post technical changelogs."
version: "1.0.0"
user-invocable: true
metadata:
  capabilities:
    - social/twitter-posting
    - social/linkedin-posting
    - social/sentiment-analysis
  author: "Antigravity (OpenPango Core)"
  license: "MIT"
---

# Social Media & Brand Growth Suite

This intrinsic skill allows OpenPango agents to execute business growth strategies autonomously. By attaching output logs, changelogs, or PR diffs, an agent can summarize technical achievements into high-converting social media posts across multiple platforms.

## Setup

Requires valid API tokens exported to the environment:
- `TWITTER_BEARER_TOKEN` or `TWITTER_API_KEY`/`SECRET`
- `LINKEDIN_ACCESS_TOKEN`

## Usage

```python
from skills.social_media.brand_manager import BrandManager

manager = BrandManager()

# Automatically generate a post based on a recent git commit
changelog = "feat(marketplace): Decentralized Skill Registry API with SQLite cache and test coverage (#49)"

manager.generate_and_post(
    topic="Product Update",
    context=changelog,
    platforms=["twitter", "linkedin"]
)

# Analyze recent sentiment
sentiment = manager.analyze_sentiment("twitter")
print(f"Current brand sentiment: {sentiment}")
```
