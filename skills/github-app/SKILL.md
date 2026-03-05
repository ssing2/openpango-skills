# GitHub App Native Integration

**Category:** Developer Tools / Automation
**Author:** XiaoXinXin (OpenClaw AI Agent)
**Version:** 1.0.0
**Status:** In Development

## Overview

Official GitHub App backend for OpenPango Skills that enables autonomous code review, bug fixes, and feature implementation through webhook-triggered OpenClaw tasks.

## Features

### 🔍 Automated Code Review
- Triggered on PR open/sync events
- Fetches PR diff and analyzes changes
- Dispatches review task to OpenClaw Coder agent
- Provides actionable feedback

### 🤖 Issue Command Handler
Responds to `@openpango` commands in issue comments:
- `@openpango fix <bug>` - Automatically fix reported bugs
- `@openpango review <target>` - Review specific code
- `@openpango implement <feature>` - Implement new features
- `@openpango explain <code>` - Explain code functionality
- `@openpango test <target>` - Write tests
- `@openpango document <target>` - Add documentation

### 🛡️ Safety Features
- Branch protection (never push to main/master)
- Webhook signature verification
- Permission scoping
- Audit logging
- Concurrent operation limits

## Architecture

```
┌─────────────┐     Webhook     ┌──────────────────┐
│   GitHub    │ ───────────────>│  FastAPI Server  │
└─────────────┘                 └──────────────────┘
                                         │
                                ┌────────┴────────┐
                                │  Event Router   │
                                └────────┬────────┘
                                         │
                    ┌────────────────────┼────────────────────┐
                    │                    │                    │
                    v                    v                    v
            ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
            │ PR Reviewer  │    │Issue Handler │    │Safety Check  │
            └──────────────┘    └──────────────┘    └──────────────┘
                    │                    │
                    v                    v
            ┌──────────────────────────────────┐
            │     OpenClaw Task Dispatcher     │
            └──────────────────────────────────┘
```

## Installation

### Prerequisites
- Python 3.9+
- FastAPI
- GitHub App credentials
- OpenClaw instance

### Setup

1. **Create GitHub App**
   ```bash
   # Go to GitHub Settings > Developer Settings > GitHub Apps
   # Create new app with following permissions:
   # - Contents: Read & Write
   # - Issues: Read & Write
   # - Pull Requests: Read & Write
   # - Webhooks: Read & Write
   ```

2. **Install Dependencies**
   ```bash
   pip install fastapi uvicorn httpx PyGithub
   ```

3. **Configure Environment**
   ```bash
   export GITHUB_APP_ID="your_app_id"
   export GITHUB_APP_SECRET="your_app_secret"
   export WEBHOOK_SECRET="your_webhook_secret"
   export GITHUB_PRIVATE_KEY="-----BEGIN RSA PRIVATE KEY-----\n..."
   export OPENCLAW_API_URL="http://localhost:3000"
   ```

4. **Run Server**
   ```bash
   cd skills/github-app
   uvicorn app:app --host 0.0.0.0 --port 8000
   ```

5. **Configure Webhook**
   - Set webhook URL: `https://your-domain.com/webhook`
   - Set webhook secret (same as WEBHOOK_SECRET)
   - Subscribe to events: pull_request, issue_comment, push

## Usage

### Automated PR Review

When a PR is opened, the app automatically:
1. Fetches the diff
2. Analyzes changes
3. Generates review feedback
4. Posts comments on the PR

### Issue Commands

Comment on any issue with `@openpango` commands:

```
@openpango fix the authentication bug in login.py
```

The app will:
1. Clone the repository
2. Analyze the issue
3. Implement the fix
4. Create a pull request

### Safety Guarantees

- ✅ Never pushes to main/master branches
- ✅ Always creates feature branches
- ✅ Requires approval for sensitive repositories
- ✅ Validates all webhook signatures
- ✅ Logs all actions for audit

## Configuration

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GITHUB_APP_ID` | Yes | GitHub App ID |
| `GITHUB_APP_SECRET` | Yes | GitHub App client secret |
| `WEBHOOK_SECRET` | Yes | Webhook verification secret |
| `GITHUB_PRIVATE_KEY` | Yes | GitHub App private key |
| `OPENCLAW_API_URL` | Yes | OpenClaw API endpoint |
| `WEBHOOK_PORT` | No | Server port (default: 8000) |
| `MAX_CONCURRENT_TASKS` | No | Max concurrent operations (default: 10) |

### Protected Branches

Configure protected branches in `services/safety.py`:

```python
PROTECTED_BRANCHES = ["main", "master", "develop", "production"]
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/webhook` | POST | GitHub webhook receiver |
| `/health` | GET | Health check |
| `/` | GET | Service info |

## Examples

### Example 1: Bug Fix

```python
# User comments on issue:
@openpango fix the null pointer exception in UserService.java

# App response:
✅ Bug fix task dispatched!
📝 Issue: #123
🌿 Branch: openpango/fix-123
⏳ Estimated time: 5 minutes
```

### Example 2: Code Review

```python
# PR opened automatically triggers review:
🔍 Analyzing PR #456...
📊 3 files changed (+127/-45)
✅ Review complete
💬 5 comments posted
```

## Security

### Webhook Verification
All webhooks are verified using HMAC-SHA256 signatures.

### Permission Scoping
App requests minimal required permissions.

### Audit Logging
All actions are logged with timestamps and details.

## Testing

```bash
# Run tests
pytest tests/

# Test webhook signature
python -c "
from webhook.signature import WebhookSignature
payload = b'{\"test\": \"data\"}'
secret = 'test_secret'
sig = WebhookSignature.generate(payload, secret)
print(f'Signature: {sig}')
print(f'Valid: {WebhookSignature.verify(payload, sig, secret)}')
"
```

## Troubleshooting

### Common Issues

**Webhook signature verification fails**
- Ensure WEBHOOK_SECRET matches GitHub App settings
- Check that raw body is used (not parsed JSON)

**Permission denied errors**
- Verify GitHub App has required permissions
- Check repository access settings

**Tasks not dispatching**
- Verify OPENCLAW_API_URL is correct
- Check OpenClaw is running and accessible

## Contributing

This skill is developed as part of OpenPango Bounty #39.

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Submit a pull request

## License

MIT License

## Changelog

### v1.0.0 (2026-03-05)
- Initial release
- PR review automation
- Issue command handler
- Safety checks
- Webhook integration

## Support

For issues and feature requests, please open an issue in the OpenPango repository.

---

**Bounty:** #39 - GitHub App Native Integration
**Reward:** $11
**Status:** In Progress
